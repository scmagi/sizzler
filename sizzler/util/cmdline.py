#!/usr/bin/env python3

import argparse

LICENSE = """
Copyright (c) 2018 Sizzler

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

#----------------------------------------------------------------------------#

EXAMPLE_CONFIG = """
# An example config file for Sizzler
# ----------------------------------
# Please edit this file according to instructions. Lines beginning with # are
# comments and will be ignored.
#
# Save this file as something like `config.yaml`, and tell Sizzler to use it
# upon starting:
#   sizzler -c config.yaml  # for starting Sizzler as a client
#   sizzler -s config.yaml  # for starting Sizzler as a server 


# This is the key for authorized access to your virtual network.
# Must be kept secret.

key: example-key

# These are IP addresses allocated in virtual network for both server and
# client.

ip:
    server: 10.1.0.1
    client: 10.1.0.2

# The server will listen on the address and port as follow.

server:
    host: localhost
    port: 8765

# The client will attempt accessing the server via following URI. This may
# differ from above server settings, especially when you desire to use e.g.
# reverse proxies.
#
# Listing multiple URIs will make client also use multiple connections.

client:
    - ws://123.1.1.1:8765   # suppose this is the server's Internet IP
    - ws://example.com/foo  # if you can redirect this to 123.1.1.1:8765
    - wss://example.org/bar # you may also use wss:// protocol
"""

#----------------------------------------------------------------------------#

def parseCommandLineArguments(args):
    global EXAMPLE_CONFIG

    parser = argparse.ArgumentParser(
        prog="sizzler",
        description="""Sizzler is a Linux tool for setting up virtually
        connected network interfaces on 2 different computers. The network
        traffic between both interfaces will be encrypted and transmitted via
        WebSocket. To enable this over Internet, one computer must behave like
        a normal HTTP/HTTPS server, which listens for incoming WebSocket
        connections, while the other works like a normal web client.""",
        epilog="""For documentation, bug and discussions, visit
        <https://github.com/scmagi/sizzler>."""
    )

    job = parser.add_mutually_exclusive_group(required=True)
    
    job.add_argument(
        "-s",
        "--server",
        metavar="CONFIG_FILE",
        type=str,
        help="""Run as a server using given config file."""
    )

    job.add_argument(
        "-c",
        "--client",
        metavar="CONFIG_FILE",
        type=str,
        help="""Run as a client using given config file."""
    )

    job.add_argument(
        "-e",
        "--example",
        action="store_true",
        help="""Print an example config file and exit."""
    )

    results = parser.parse_args(args)

    if results.example:
        print(EXAMPLE_CONFIG)
        exit()
        
    return results
