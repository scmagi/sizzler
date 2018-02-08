#!/usr/bin/env python3

import asyncio
import websockets
import time
import sys

from ._wssession import WebsocketSession
from ._transport import SizzlerTransport


class WebsocketServer(SizzlerTransport):

    def __init__(self, host=None, port=None, key=None):
        SizzlerTransport.__init__(self)
        self.host = host
        self.port = port
        self.key = key

    async def __wsHandler(self, websocket, path):
        print("New connection: %s" % path)
        try:
            self.increaseConnectionsCount()
            await WebsocketSession(
                websocket=websocket,
                path=path,
                key=self.key,
                fromWSQueue=self.fromWSQueue,
                toWSQueue=self.toWSQueue
            )
        except Exception as e:
            print(e)
        finally:
            self.decreaseConnectionsCount()
            print("One connection closed. Alive connections: %d" % \
                self.connections
            )

    def __await__(self):
        assert self.toWSQueue != None and self.fromWSQueue != None
        yield from websockets.serve(self.__wsHandler, self.host, self.port)
