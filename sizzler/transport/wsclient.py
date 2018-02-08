#!/usr/bin/env python3

import asyncio
import websockets
import os
import sys
import time

import yaml

from ._wssession import WebsocketSession
from ._transport import SizzlerTransport


class WebsocketClient(SizzlerTransport):

    def __init__(self, uris=None, key=None):
        SizzlerTransport.__init__(self)
        self.uris = uris
        self.key = key

    async def __connect(self, baseURI):
        while True:
            try:
                uri = baseURI
                if not uri.endswith("/"): uri += "/"
                uri += "?_=%s" % os.urandom(32).hex()
                async with websockets.connect(uri) as websocket:
                    self.increaseConnectionsCount()
                    await WebsocketSession(
                        websocket=websocket,
                        path=uri,
                        key=self.key,
                        fromWSQueue=self.fromWSQueue,
                        toWSQueue=self.toWSQueue
                    )
            except Exception as e:
                print(e)
            finally:
                self.decreaseConnectionsCount()
                print("Connection failed or broken. Try again in 5 seconds.")
                await asyncio.sleep(5)

    def __await__(self):
        assert self.toWSQueue != None and self.fromWSQueue != None
        services = [self.__connect(uri) for uri in self.uris]
        yield from asyncio.gather(*services)
