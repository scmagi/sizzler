#!/usr/bin/env python3

import asyncio
import os
import sys
import time

import yaml

from ._tcpsession import TCPSession 
from ._transport import SizzlerTransport


class TCPClient(SizzlerTransport):

    def __init__(self, addrs=None, key=None):
        SizzlerTransport.__init__(self)
        self.addrs = addrs
        self.key = key

    async def __connect(self, addr):
        while True:
            try:
                async with asyncio.open_connection(addr[0], addr[1]) as rw:
                    reader, writer = rw
                    self.increaseConnectionsCount()
                    await TCPSession(
                        reader=reader,
                        writer=writer,
                        key=self.key,
                        fromWSQueue=self.fromWSQueue,
                        toWSQueue=self.toWSQueue
                    )
            except Exception as e:
                print(e)
            finally:
                writer.close()
                reader.close()
                self.decreaseConnectionsCount()
                print("Connection failed or broken. Try again in 5 seconds.")
                await asyncio.sleep(5)

    def __await__(self):
        assert self.toWSQueue != None and self.fromWSQueue != None
        services = [self.__connect(addr) for addr in self.addrs]
        yield from asyncio.gather(*services)
