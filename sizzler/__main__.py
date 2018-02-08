#!/usr/bin/env python3

import os
import sys
import asyncio

from .util.root import RootPriviledgeManager
from .util.cmdline import parseCommandLineArguments
from .config.parser import loadConfigFile
from .tun import SizzlerVirtualNetworkInterface
from .transport.wsserver import WebsocketServer
from .transport.wsclient import WebsocketClient

"""
------------------------------------------------------------------------------
Parse command line arguments.
"""

argv = parseCommandLineArguments(sys.argv[1:])

ROLE = "server" if argv.server else "client"
CONFIG = loadConfigFile(argv.server if ROLE == "server" else argv.client)

"""
------------------------------------------------------------------------------
We need root priviledge.
"""

priviledgeManager = RootPriviledgeManager()
if not priviledgeManager.isRoot():
    print("Error: you need to run sizzler with root priviledge.")
    exit(1)

"""
------------------------------------------------------------------------------
With root priviledge, we have to set up TUN device as soon as possible.
"""

tun = SizzlerVirtualNetworkInterface(
    ip=CONFIG["ip"]["client" if ROLE == "client" else "server"],
    dstip=CONFIG["ip"]["server" if ROLE == "client" else "client"]
)

"""
------------------------------------------------------------------------------
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
------------------------------------------------------------------------------
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
------------------------------------------------------------------------------
Start event loop.
"""

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(tun, transport))
