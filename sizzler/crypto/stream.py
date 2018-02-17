#!/usr/bin/env python3

import asyncio
import hashlib
import hmac

from Crypto.Cipher import AES
from Crypto.Util import Counter


def getStreamCipher(key, nonce):
    if type(key) == str: key = key.encode('utf-8')
    assert type(key) == bytes
    
    key = hashlib.sha512(key).digest()
    aes = AES.new(
        hmac.new(key, nonce, hashlib.sha256).digest(),
        AES.MODE_CTR,
        b"",
        Counter.new(128, initial_value=0)
    )
    
    loop = asyncio.get_event_loop()
    async def encrypt(data):
        future = loop.run_in_executor(None, aes.encrypt, data)
        return await future
    async def decrypt(data):
        future = loop.run_in_executor(None, aes.decrypt, data)
        return await future

    return (encrypt, decrypt)
