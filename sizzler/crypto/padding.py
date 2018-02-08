#!/usr/bin/env python3

import os
import asyncio
import random


# tell calculation how many bytes will be added after encryption with respect
# to input before padding

PADDING_FORMAT_OVERHEAD = 2
ENCRYPTION_OVERHEAD = 40

PADDING_TOTAL_OVERHEAD = ENCRYPTION_OVERHEAD + PADDING_FORMAT_OVERHEAD


class RandomPadding:
    
    def __init__(self, targetSize=4096):
        assert targetSize > PADDING_TOTAL_OVERHEAD
        self.maxAfterPaddingLength = targetSize - PADDING_TOTAL_OVERHEAD
        self.paddingTemplate = os.urandom(65536)

    def __int16ToBytes(self, int16):
        return bytes([int16 & 0x00FF, (int16 & 0xFF00) >> 8])

    def __bytesToInt16(self, b):
        return b[0] + (b[1] << 8)

    def pad(self, data):
        dataLength = len(data)
        if dataLength >= self.maxAfterPaddingLength:
            return self.__int16ToBytes(dataLength) + data
        else:
            targetLength = random.randint(
                dataLength, self.maxAfterPaddingLength
            )
            paddingLength = targetLength - dataLength
            padding = self.paddingTemplate[:paddingLength]
            return self.__int16ToBytes(dataLength) + data + padding

    def unpad(self, data):
        dataLength = self.__bytesToInt16(data[:2])
        if dataLength > len(data) - 2: return None
        return data[2:2+dataLength]

    def __await__(self):
        while True:
            self.paddingTemplate = os.urandom(65536)
            yield from asyncio.sleep(5) # change random padding every 5 sec


if __name__ == "__main__":
    async def main():
        p = RandomPadding(100)
        print(p.pad(b"aaa"*10))

        

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
        
