#!/usr/bin/env python3

"""
Bare TCP connection for Sizzler
-------------------------------

TCP connections are made to a server port. Each connection has a random nonce
sent as the first STREAM_NONCE_LENGTH(=64 for now) bytes. After that, a stream
cipher for this connection with keys derivable on both side can be used.

Within a stream, data packets, heartbeat packets and random bytes are
transferred. Since the underlying stream cipher does not provide any
authentication, packets have to be encrypted again using the same NaCl
cipher(Salsa20+Poly1305) as with WebSocket connections.

Heartbeating provides a way of detecting if any side has lost the ability
to communicate further on a given connection. It also provides some level
of anti-replay attacks, by incorporating an (per connection) unique ID into
each packet. This ID is in fact the HEX representation of the nonce given by
outgoing connection, which is however obfuscated by the underlying Salsa20
cipher over time and therefore cannot be manipulated very successfully.
"""



import time
import asyncio
import hashlib
import os
import base64

from ..crypto.crypto import getCrypto
from ..crypto.stream import getStreamCipher
from ..crypto.padding import RandomPadding


tcpid = 0

TIMEDIFF_TOLERANCE = 300
CONNECTION_TIMEOUT = 30
STREAM_NONCE_LENGTH = 64
PADDING_MAX = 2048

class TCPSession:

    tcpid = 0

    def __init__(self, reader, writer, key, fromWSQueue, toWSQueue):
        global tcpid
        tcpid += 1
        self.tcpid = tcpid
        self.reader = reader
        self.writer = writer
        self.fromWSQueue = fromWSQueue
        self.toWSQueue = toWSQueue
        
        self.key = key
        self.packetEncryptor, self.packetDecryptor = getCrypto(key)
        self.padder = RandomPadding(PADDING_MAX) 
        self.outgoingID, self.incomingID = None, None # will be changed on run
        self.outgoingReady = False # heartbeat pauses until stream established
        self.incomingBuffer = b""

        # parameters for heartbeating
        self.peerAuthenticated = False
        self.lastHeartbeat = time.time()

    # ---- Before sending any packet
    #      Either data or heartbeat packet must be processed using this
    #      method. Data packet will be properly random padded, encoded and
    #      added with "\n" separators.

    async def __beforeSend(self, data=None, heartbeat=None):
        # Pack plaintext with headers etc. Returns packed data if they are
        # ok for outgoing traffic, or None.
        ret = None
        if data:
            ret = b"d-" + data
        if heartbeat:
            ret = ("h-%s-%s" % (self.outgoingID, time.time())).encode('ascii')
        padded = self.padder.pad(ret)
        encrypted = await self.packetEncryptor(padded)
        return b"\n" + base64.b85encode(encrypted) + b"\n"

    async def __afterReceive(self, raw):
        self.incomingBuffer += raw
        if not b"\n" in self.incomingBuffer: 
            return None
        divided = self.incomingBuffer.split(b"\n")
        self.incomingBuffer = divided[-1]
        for chunk in divided[:-1]:
            try:
                decrypted = await self.packetDecryptor(base64.b85decode(chunk))
                raw = self.padder.unpad(decrypted)
                if not raw: return None
            except:
                return None
            if raw.startswith(b"d-"):
                data = raw[2:]
                self.fromWSQueue.put(data)
                print("hi")
            if raw.startswith(b"h-"):
                print(raw)
                self.__heartbeatReceived(raw)
                return None

    # ---- Heartbeat to remote, and evaluation of remote sent heartbeats.

    def __heartbeatReceived(self, raw):
        # If a remote heartbeat received, record its timestamp.
        try:
            heartbeatSlices = raw.decode('ascii').split('-')
            assert heartbeatSlices[0] == "h"
            assert heartbeatSlices[1] == self.incomingID
            timestamp = float(heartbeatSlices[2])
            nowtime = time.time()
            if timestamp <= nowtime + TIMEDIFF_TOLERANCE:
                self.lastHeartbeat = max(self.lastHeartbeat, timestamp)
                self.peerAuthenticated = True
        except:
            print("Warning: invalid heartbeat!")

    async def __sendLocalHeartbeat(self):
        # Try to send local heartbeats.
        while True:
            if self.outgoingReady:
                d = await self.__beforeSend(heartbeat=True)
                e = await self.packetEncryptor(d)
                self.writer.write(e)
            await asyncio.sleep(2)

    async def __checkRemoteHeartbeat(self):
        # See if remote to us is still alive. If not, raise Exception and
        # terminate the connections.
        while True:
            await asyncio.sleep(5)
            if time.time() - self.lastHeartbeat > CONNECTION_TIMEOUT:
                raise Exception("Connection %d timed out." % self.tcpid)

    # ---- Streaming sending and receiving
    #
    #      Task: encrypt and decrypt outgoing/incoming stream. For outgoing
    #            stream, inject random bytes between each encoded packets.
    #            For incoming stream, try to buffer and verify packets.
    #            

    async def __outgoingStreaming(self):
        # Decide encryption for outgoing stream. Send nonce first.
        nonce = os.urandom(STREAM_NONCE_LENGTH)
        self.__encryptor, _ = getStreamCipher(self.key, nonce)
        self.outgoingID = nonce.hex()
        self.writer.write(nonce)
        # After that, send packets and random bytes
        self.outgoingReady = True
        while True:
            d = await self.toWSQueue.get()      # data to be sent ready
            s = await self.__beforeSend(data=d) # pack the data
            if s:
                e = await self.__encryptor(s)
                self.writer.write(e)

    async def __incomingStreaming(self):
        # Listens for the first bytes for a nonce
        nonce = await self.reader.readexactly(STREAM_NONCE_LENGTH)
        self.incomingID = nonce.hex()
        _, self.__decryptor = getStreamCipher(self.key, nonce)
        # After nonce is available, do regular receiving
        while True:
            d = await self.reader.read(1024)
            d = await self.__decryptor(d)
            await self.__afterReceive(d)

    def __await__(self):
        yield from asyncio.gather(
            self.__outgoingStreaming(),
            self.__incomingStreaming(),
            self.__sendLocalHeartbeat(),
            self.__checkRemoteHeartbeat(),
            self.padder
        )
