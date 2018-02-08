#!/usr/bin/env python3

import asyncio
import os
import random
import struct
import time


# tell calculation how many bytes will be added after encryption with respect
# to input before padding

PADDING_FORMAT_OVERHEAD = 2 + 8
ENCRYPTION_OVERHEAD = 40

PADDING_TOTAL_OVERHEAD = ENCRYPTION_OVERHEAD + PADDING_FORMAT_OVERHEAD

# How many nonces may be (theoretically) issued per second, limits the max.
# network speed!
NONCES_RESOLUTION = 1e6 # < if packet size = 4kB, limits to 4GB/s(???)
DELETE_NONCES_BEFORE = 300 * NONCES_RESOLUTION


class NonceManagement:

    def __init__(self):
        self.nonces = []

    def new(self):
        return int(time.time() * NONCES_RESOLUTION)

    def verify(self, nonce):
        if not self.nonces:
            self.nonces.append(nonce)
            self.oldest = nonce - DELETE_NONCES_BEFORE
            return True
        if nonce < self.oldest or nonce in self.nonces:
            print("Nonce failure: Replay attack or unexpected bug!")
            return False
        self.nonces.append(nonce)
        return True

    def __await__(self):
        while True:
            # recalculate acceptable nonce time
            if self.nonces:
                self.oldest = max(self.nonces) - DELETE_NONCES_BEFORE
                # clear nonces cache
                self.nonces = [e for e in self.nonces if e >= self.oldest]
            yield from asyncio.sleep(30)


class RandomPadding:
    
    def __init__(self, targetSize=4096):
        assert targetSize > PADDING_TOTAL_OVERHEAD
        self.maxAfterPaddingLength = targetSize - PADDING_TOTAL_OVERHEAD
        self.paddingTemplate = os.urandom(65536)
        self.nonces = NonceManagement()

    def __packHead(self, dataLength):
        # put `dataLength` and nonce(timestamp-based) into a header
        return struct.pack("<HQ", dataLength, self.nonces.new())

    def __unpackHead(self, data):
        # unpack header, extract nonce and dataLength.
        dataLength, nonce = struct.unpack("<HQ", data)
        # verify nonce, if invalid, drop it internally
        if self.nonces.verify(nonce):
            return dataLength
        else:
            return None

    def pad(self, data):
        dataLength = len(data)
        if dataLength >= self.maxAfterPaddingLength:
            return self.__packHead(dataLength) + data
        else:
            targetLength = random.randint(
                dataLength, self.maxAfterPaddingLength
            )
            paddingLength = targetLength - dataLength
            padding = self.paddingTemplate[:paddingLength]
            return self.__packHead(dataLength) + data + padding

    def unpad(self, data):
        dataLength = self.__unpackHead(data[:PADDING_FORMAT_OVERHEAD])
        if not dataLength: return None
        if dataLength > len(data) - PADDING_FORMAT_OVERHEAD: return None
        return data[PADDING_FORMAT_OVERHEAD:][:dataLength]

    def __await__(self):
        async def job1():
            while True:
                self.paddingTemplate = os.urandom(65536)
                await asyncio.sleep(5) # change random padding every 5 sec
        yield from asyncio.gather(job1(), self.nonces)


if __name__ == "__main__":
    async def main():
        p = RandomPadding(100)
        print(p.pad(b"aaa"*10))

        

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
        
