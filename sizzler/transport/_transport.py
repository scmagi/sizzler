#!/usr/bin/env python3

class SizzlerTransport:

    def __init__(self):
        self.connections = 0
        self.toWSQueue, self.fromWSQueue = None, None

    def increaseConnectionsCount(self):
        self.connections += 1

    def decreaseConnectionsCount(self):
        self.connections -= 1
