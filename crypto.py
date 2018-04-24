from Crypto.Hash import MD5
from Crypto.Cipher import AES
from Crypto import Random

import base64

def get_md5(data):
    md5 = MD5.new()
    md5.update(data.encode())
    return md5.hexdigest()

def get_aeskey():
    aeskey = Random.new().read(AES.block_size)
    return base64.b64encode(aeskey)

iv = Random.new().read(AES.block_size)

length = 16

#补齐最后一块数据
#如补1个/x01，5个/x05,16个/x0h

def utf8len(s):
    if isinstance(s, bytes):
        return len(s)
    return len(s.encode('utf-8'))

pad = lambda s: s + (length - utf8len(s) % length) * chr(length - utf8len(s) % length)

# def pad(msg):
#     msg = msg + (length - len(msg) % length) * str(length - len(msg) % length)
#     return msg.encode('utf-8')

unpad = lambda s: s[0:-ord(chr(s[-1]))]

# def unpad(msg):
#     while msg[-1] == '{':
#         msg = msg[:-1]
#         print(len(msg))

def encrypt(msg, key):
    key = base64.b64decode(key)
    cbc_cipher = AES.new(key, AES.MODE_CBC, IV=iv)
    cipher_text = iv + cbc_cipher.encrypt(pad(msg))
    return base64.b64encode(cipher_text)

def decrypt(msg, key):
    key = base64.b64decode(key)
    cipher_text = base64.b64decode(msg)
    cbc_decipher = AES.new(key, AES.MODE_CBC, IV=cipher_text[:length])
    decrypt_text = cbc_decipher.decrypt(cipher_text[16:])
    return unpad(decrypt_text)

if __name__ == "__main__":
    msg = '123'
    print(utf8len(u'a'))
    key = base64.b64decode(get_aeskey())
    encrypt_text = encrypt(msg, key)
    decrypt_text = decrypt(encrypt_text, key)
    print(len(encrypt_text))
    print(decrypt_text.decode('utf-8'))
