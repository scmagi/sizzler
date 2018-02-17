#!/usr/bin/env python3

"""
------------------------------------------------------------------------------
Check running environment:
    * ensure running under Python 3.5+;
    * ensure 3rd party packages installed.
"""

import sys
if sys.version_info < (3, 5):
    print("Error: you have to run Sizzler with Python 3.5 or higher version.")
    exit(1)

try:
    import websockets
    import nacl
    import yaml
    import Crypto
except:
    print("Error: one or more 3rd party package(s) not installed.")
    print("To fix this, run:\n sudo pip3 install -r requirements.txt")
    exit(1)

import os
import asyncio

from .util.root import RootPriviledgeManager
from .util.cmdline import parseCommandLineArguments
from .config.parser import loadConfigFile
from .tun import SizzlerVirtualNetworkInterface
from .transport.wsserver import WebsocketServer
from .transport.wsclient import WebsocketClient
from .transport.tcpserver import TCPServer
from .transport.tcpclient import TCPClient

def main():

    """
    --------------------------------------------------------------------------
    Parse command line arguments.
    """

    argv = parseCommandLineArguments(sys.argv[1:])

    ROLE = "server" if argv.server else "client"
    CONFIG = loadConfigFile(argv.server if ROLE == "server" else argv.client)

    """
    --------------------------------------------------------------------------
    We need root priviledge.
    """

    priviledgeManager = RootPriviledgeManager()
    if not priviledgeManager.isRoot():
        print("Error: you need to run sizzler with root priviledge.")
        exit(1)

    """
    --------------------------------------------------------------------------
    With root priviledge, we have to set up TUN device as soon as possible.
    """

    tun = SizzlerVirtualNetworkInterface(
        ip=CONFIG["ip"]["client" if ROLE == "client" else "server"],
        dstip=CONFIG["ip"]["server" if ROLE == "client" else "client"]
    )

    """
    --------------------------------------------------------------------------
    Now root is no longer required.
    """

    try:
        priviledgeManager.dropRoot()
        assert not priviledgeManager.isRoot()
    except Exception as e:
        print("Error: failed dropping root priviledge.")
        print(e)
        exit(1)

    """
    --------------------------------------------------------------------------
    Start the server or client.
    """

    transportConfig = CONFIG[ROLE]
    initializers = {
        ("server", "ws"): lambda p: WebsocketServer(
            host=p["host"], port=p["port"], key=CONFIG["key"]),
        ("server", "tcp"): lambda p: TCPServer(
            addr=(p["host"], p["port"]), key=CONFIG["key"]),
        ("client", "ws"): lambda p: WebsocketClient(
            uris=p, key=CONFIG["key"]),
        ("client", "tcp"): lambda p: TCPClient(
            addrs=p, key=CONFIG["key"]),
    }

    transports = []

    for transportType in transportConfig:
        try:
            initializer = initializers[(ROLE, transportType)]
        except:
            print("Invalid config file: %s is not a known transport type." %
                transportType)
            exit(1)
        transport = initializer(transportConfig[transportType])
        tun.connect(transport)
        transports.append(transport)

    """
    --------------------------------------------------------------------------
    Start event loop.
    """

    print("Running Sizzler now...")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(tun, *transports))


if __name__ == "__main__":
    main()
