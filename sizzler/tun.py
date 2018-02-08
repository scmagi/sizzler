#!/usr/bin/env python3

import os
import fcntl
import struct
import asyncio
from logging import info, debug, critical, exception

from .transport._transport import SizzlerTransport

TUNSETIFF = 0x400454ca  
IFF_TUN   = 0x0001      # Set up TUN device
IFF_TAP   = 0x0002      # Set up TAP device
IFF_NO_PI = 0x1000      # Without this flag, received frame will have 4 bytes
                        # for flags and protocol(each 2 bytes)

def _getTUNDeviceLocation():
    if os.path.exists("/dev/net/tun"): return "/dev/net/tun"
    if os.path.exists("/dev/tun"): return "/dev/tun"
    critical("TUN/TAP device not found on this OS!")
    raise Exception("No TUN/TAP device available.")

def _getReader(tun):
    loop = asyncio.get_event_loop()
    async def read():
        future = loop.run_in_executor(None, os.read, tun, 65536)
        return await future
    return read

def _getWriter(tun):
    loop = asyncio.get_event_loop()
    async def write(data):
        future = loop.run_in_executor(
            None,
            os.write,
            tun,
            data
        )
        await future
    return write


class SizzlerVirtualNetworkInterface:

    def __init__(self, ip, dstip, mtu=1500, netmask="255.255.255.0"):
        self.ip = ip
        self.dstip = dstip
        self.mtu = mtu
        self.netmask = netmask
        self.__tunR, self.__tunW = self.__setup()
        self.toWSQueue = asyncio.Queue()
        self.fromWSQueue = asyncio.Queue()
        self.transports = []

    def __setup(self):
        try:
            self.tun = os.open(_getTUNDeviceLocation(), os.O_RDWR)
            ret = fcntl.ioctl(\
                self.tun,
                TUNSETIFF,
                struct.pack("16sH", b"sizzler-%d", IFF_TUN)
            )
            tunName = ret[:16].decode("ascii").strip("\x00")
            info("Virtual network interface [%s] created." % tunName)

            os.system("ifconfig %s inet %s netmask %s pointopoint %s" %
                (tunName, self.ip, self.netmask, self.dstip)
            )
            os.system("ifconfig %s mtu %d up" % (tunName, self.mtu))
            info(
                """%s: mtu %d  addr %s  netmask %s  dstaddr %s""" %
                (tunName, self.mtu, self.ip, self.netmask, self.dstip)
            )

            return _getReader(self.tun), _getWriter(self.tun)
        except Exception as e:
            exception(e)
            raise Exception("Cannot set TUN/TAP device.")

    def connect(self, transport):
        assert isinstance(transport, SizzlerTransport)
        self.transports.append(transport)
        transport.fromWSQueue = self.fromWSQueue
        transport.toWSQueue = self.toWSQueue

    def __countAvailableTransports(self):
        count = sum([each.connections for each in self.transports])
        return count

    def __await__(self):
        async def proxyQueueToTUN():
            while True:
                s = await self.fromWSQueue.get()
                await self.__tunW(s)
        async def proxyTUNToQueue():
            while True:
                s = await self.__tunR()
                if self.__countAvailableTransports() < 1: continue
                await self.toWSQueue.put(s)
        yield from asyncio.gather(proxyQueueToTUN(), proxyTUNToQueue())
