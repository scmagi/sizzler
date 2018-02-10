#!/usr/bin/env python3

import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Sizzler",
    version = "0.0.1",
    author = "Sogisha",
    author_email = "sogisha@protonmail.com",
    description = ("A VPN over WebSocket"),
    license = "MIT",
    keywords = "asyncio VPN WebSocket TUN",
    url = "http://github.com/scmagi/sizzler",
    packages=find_packages(),
    long_description=read('README.md'),
    entry_points="""
    [console_scripts]
    sizzler=sizzler.__main__:main
    """
)
