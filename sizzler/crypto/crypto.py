#!/usr/bin/env python3

import asyncio
import hashlib
import nacl.secret

def __getEncryptor(box):
    loop = asyncio.get_event_loop()
    async def encrypt(data):
        future = loop.run_in_executor(None, box.encrypt, data)
        return await future
    return encrypt

def __getDecryptor(box):
    loop = asyncio.get_event_loop()
    async def decrypt(data):
        def _wrapDecrypt(data):
            try:
                return box.decrypt(data)
            except:
                return None
        future = loop.run_in_executor(None, _wrapDecrypt, data)
        return await future
    return decrypt



def getCrypto(key):
    if type(key) == str: key = key.encode('utf-8')
    assert type(key) == bytes
    
    encryptKey = hashlib.sha512(key).digest()
    authkey = hashlib.sha512(encryptKey).digest()

    encryptKey = encryptKey[:nacl.secret.SecretBox.KEY_SIZE]

    box = nacl.secret.SecretBox(encryptKey)

    return __getEncryptor(box), __getDecryptor(box)



if __name__ == "__main__":
    async def main():
        encryptor, decryptor = getCrypto("test")
        d = await encryptor(b"plaintext")
        print(d)
        d = await decryptor(d)
        print(d)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
        
