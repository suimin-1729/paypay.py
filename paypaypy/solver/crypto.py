import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

key = bytes.fromhex("6f71a512b1e035eaab53d8be73120d3fb68a0ca346b9560aab3e5cdf753d5e98")
aes_gcm = AESGCM(key)

class Crypto:
    @staticmethod
    def encrypt(string):
        iv = os.urandom(12)

        encrypted = aes_gcm.encrypt(iv, string, None)

        tag = encrypted[-16:]
        text = encrypted[:-16]

        iv_base64 = base64.b64encode(iv).decode("utf-8")

        return f"{iv_base64}::{tag.hex()}::{text.hex()}"
    
    @staticmethod
    def decrypt(string):
        encrypted_parts = string.split("::")
        iv_base64_part = encrypted_parts[0]
        tag_hex_part = encrypted_parts[1]
        text_hex_part = encrypted_parts[2]

        iv_part = base64.b64decode(iv_base64_part)
        tag_part = bytes.fromhex(tag_hex_part)
        text_part = bytes.fromhex(text_hex_part)

        return aes_gcm.decrypt(iv_part, text_part + tag_part, None)