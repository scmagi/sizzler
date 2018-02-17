#!/usr/bin/env python3

import asyncio
import websockets
import time
import sys

from ._tcpsession import TCPSession
from ._transport import SizzlerTransport


class TCPServer(SizzlerTransport):

    def __init__(self, addr=None, key=None):
        SizzlerTransport.__init__(self)
        self.addr = addr
        self.key = key

    async def __tcpHandler(self, reader, writer):
        try:
            self.increaseConnectionsCount()
            await TCPSession(
                writer=writer,
                reader=reader,
                key=self.key,
                fromWSQueue=self.fromWSQueue,
                toWSQueue=self.toWSQueue
            )
        except Exception as e:
            print(e)
        finally:
#            reader.close()
#            writer.close()
            self.decreaseConnectionsCount()
            print("One connection closed. Alive connections: %d" % \
                self.connections
            )

    def __await__(self):
        assert self.toWSQueue != None and self.fromWSQueue != None
        yield from asyncio.start_server(self.__tcpHandler, *self.addr)
