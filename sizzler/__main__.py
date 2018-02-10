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

    if ROLE == "client":
        transport = WebsocketClient(uris=CONFIG["client"], key=CONFIG["key"])

    else:
        transport = WebsocketServer(
            host=CONFIG["server"]["host"],
            port=CONFIG["server"]["port"],
            key=CONFIG["key"]
        )

    tun.connect(transport)

    """
    --------------------------------------------------------------------------
    Start event loop.
    """

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(tun, transport))


if __name__ == "__main__":
    main()
