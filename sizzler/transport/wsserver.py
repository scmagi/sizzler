#!/usr/bin/env python3

import asyncio
import websockets
import time
import sys
from logging import info, debug, critical, exception

from ._wssession import WebsocketSession
from ._transport import SizzlerTransport


class WebsocketServer(SizzlerTransport):

    def __init__(self, host=None, port=None, key=None):
        SizzlerTransport.__init__(self)
        self.host = host
        self.port = port
        self.key = key

    async def __wsHandler(self, websocket, path):
        info("New connection: %s" % path)
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
            debug("Server connection break, reason: %s" % e)
        finally:
            self.decreaseConnectionsCount()
            info("Current alive connections: %d" % self.connections)

    def __await__(self):
        assert self.toWSQueue != None and self.fromWSQueue != None
        yield from websockets.serve(self.__wsHandler, self.host, self.port)
