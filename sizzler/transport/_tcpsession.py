#!/usr/bin/env python3

import time
import asyncio
import hashlib
import os 

from ..crypto.crypto import getCrypto


tcpid = 0

TIMEDIFF_TOLERANCE = 300
CONNECTION_TIMEOUT = 30
STREAM_NONCE_LENGTH = 64

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
        self.encryptor, self.decryptor = getCrypto(key)

        self.outgoingNonce = os.urandom(STREAM_NONCE_LENGTH)
        self.incomingNonce = None

        # parameters for heartbeating
        self.peerAuthenticated = False
        self.lastHeartbeat = time.time()


    def __beforeSend(self, data=None, heartbeat=None):
        # Pack plaintext with headers etc. Returns packed data if they are
        # ok for outgoing traffic, or None.
        ret = None
        if data:
            ret = b"d-" + data
        if heartbeat:
            ret = ("h-%s-%s" % (self.uniqueID, time.time())).encode('ascii')
        return self.padder.pad(ret)

    def __afterReceive(self, raw):
        # unpack decrypted PLAINTEXT and extract headers etc.
        # returns data needed to be written to TUN if any, otherwise None.
        raw = self.padder.unpad(raw)
        if not raw: return None
        if raw.startswith(b"d-"):
            return raw[2:]
        if raw.startswith(b"h-"):
            self.__heartbeatReceived(raw)
            return None

    # ---- Heartbeat to remote, and evaluation of remote sent heartbeats.

    def __heartbeatReceived(self, raw):
        # If a remote heartbeat received, record its timestamp.
        try:
            heartbeatSlices = raw.decode('ascii').split('-')
            assert heartbeatSlices[0] == "h"
            assert heartbeatSlices[1] == self.uniqueID
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
            d = self.__beforeSend(heartbeat=True)
            e = await self.encryptor(d)
            await self.websocket.send(e)
            await asyncio.sleep(5)

    async def __checkRemoteHeartbeat(self):
        # See if remote to us is still alive. If not, raise Exception and
        # terminate the connections.
        while True:
            await asyncio.sleep(5)
            if time.time() - self.lastHeartbeat > CONNECTION_TIMEOUT:
                raise Exception("Connection %d timed out." % self.tcpid)


    # ---- Data transfer

    async def __receiveToQueue(self):
        while True:
            e = await self.websocket.recv()     # data received
            raw = await self.decryptor(e)
            if not raw: continue                # decryption must success
            d = self.__afterReceive(raw)
            if not d: continue                  # if any data writable to TUN
            if self.peerAuthenticated:          # if peer authenticated
                await self.fromWSQueue.put(d)
            print("               --|%3d|%s Local  %5d bytes" % (
                self.tcpid,
                "--> " if self.peerAuthenticated else "-//-",
                len(e)
            ))

    async def __sendFromQueue(self):
        while True:
            d = await self.toWSQueue.get()      # data to be sent ready
            s = self.__beforeSend(data=d)       # pack the data
            if not s: continue                  # if packer refuses, drop it
            e = await self.encryptor(s)         # encrypt packed data
            await self.websocket.send(e)        # send it
            print("   Internet   <--|%3d|--          %5d bytes" % (
                self.tcpid,
                len(s)
            ))


    # ---- Streaming sending and receiving
    #
    #      Task: encrypt and decrypt outoing/incoming stream, pack/unpack
    #            buffered data packets. If decryption failed, break the
    #            connection.

    async def __outgoingStreaming(self):
        await self.writer.write(self.outgoingNonce)

    async def __incomingStreaming(self):
        self.incomingNonce = await self.reader.read(STREAM_NONCE_LENGTH)


    def __await__(self):
        yield from asyncio.gather(
            self.__outgoingStreaming(),
            self.__incomingStreaming()
#            self.__receiveToQueue(),
#            self.__sendFromQueue(),
#            self.__sendLocalHeartbeat(),
#            self.__checkRemoteHeartbeat()
        )
