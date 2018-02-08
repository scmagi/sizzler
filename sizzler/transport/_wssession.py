#!/usr/bin/env python3

import time
import asyncio
import hashlib

from ..crypto.crypto import getCrypto
from ..crypto.padding import RandomPadding


wsid = 0

TIMEDIFF_TOLERANCE = 300
CONNECTION_TIMEOUT = 30
PADDING_MAX = 2048

class WebsocketSession:

    wsid = 0

    def __init__(
        self,
        websocket,
        path,
        key,
        fromWSQueue,
        toWSQueue
    ):
        global wsid
        wsid += 1
        self.wsid = wsid
        self.websocket = websocket
        self.fromWSQueue = fromWSQueue
        self.toWSQueue = toWSQueue
        self.encryptor, self.decryptor = getCrypto(key)
        self.padder = RandomPadding(PADDING_MAX) 

        # get path, which is the unique ID for this connection
        try:
            f = path.find("?")
            assert f >= 0
            self.uniqueID = hashlib.sha512(
                path[f:].encode("ascii")
            ).hexdigest()
        except:
            raise Exception("Connection %d without valid ID." % self.wsid)

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
                raise Exception("Connection %d timed out." % self.wsid)


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
                self.wsid,
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
                self.wsid,
                len(s)
            ))

    def __await__(self):
        yield from asyncio.gather(
            self.__receiveToQueue(),
            self.__sendFromQueue(),
            self.__sendLocalHeartbeat(),
            self.__checkRemoteHeartbeat(),
            self.padder
        )
