#-*- coding: utf-8 -*-
import base64
import hashlib
from Crypto.Cipher import AES
import json

key = "pangishandsome"
BS = 16
pad = (lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode())
unpad = (lambda s: s[:-ord(s[len(s)-1:])])


class AESCipher(object):
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, message):
        message = message.encode()
        raw = pad(message)
        cipher = AES.new(self.key, AES.MODE_CBC, self.__iv().encode('utf-8'))
        enc = cipher.encrypt(raw)
        return base64.b64encode(enc).decode('utf-8')

    def decrypt(self, enc):
        print("DECRYPT1 : ",enc) # test
        enc = base64.b64decode(enc)
        print("DECRYPT2 : ",enc) # test
        cipher = AES.new(self.key, AES.MODE_CBC, self.__iv().encode('utf-8'))
        dec = cipher.decrypt(enc)
        print("DECRYPT3 : ",dec) # test
        try:
            return unpad(dec).decode('utf-8')
        except Exception as e:
            print("err in cipher:", e)
            error = {"msg":"Decrypt Error!"}
            return json.dumps(error)

    def __iv(self):
        return chr(0) * 16

def packet_encrypt(message):
    aes = AESCipher(key)
    encrypt = aes.encrypt(message)
    return encrypt

def packet_decrypt(message):
    aes = AESCipher(key)
    decrypt = aes.decrypt(message)
    return decrypt
