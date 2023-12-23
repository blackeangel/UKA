import dataclasses
import hashlib
import binascii

from .CryptoCredential import CryptoCredential

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'

KEY_SIZE = 0x10


@dataclasses.dataclass
class OfpMtkConfiguration:
    keys: list[CryptoCredential]

    @staticmethod
    def _shuffle(obs_key, aes_key):
        new_key = bytearray()
        for index in range(0, KEY_SIZE):
            tmp_key = obs_key[index % KEY_SIZE] ^ aes_key[index]
            new_key.append(((tmp_key & 0xF0) >> 4) | (16 * (tmp_key & 0xF)))

        return new_key

    def __post_init__(self):
        result = list()
        for item in self.keys:
            obs_key = item.get('ObsKey', None)
            aes_key = item.get('AesKey', None)
            aes_iv = item.get('AesIv', None)

            if not obs_key and (aes_key and aes_key != "") and (aes_iv and aes_iv != ""):
                result.append(CryptoCredential(key=aes_key.encode('utf-8'), iv=aes_iv.encode('utf-8')))
                continue

            if (obs_key and obs_key != "") and (aes_key and aes_key != "") and (aes_iv and aes_iv != ""):
                key = (hashlib.md5(self._shuffle(bytearray.fromhex(obs_key), bytearray.fromhex(aes_key))).hexdigest()[:KEY_SIZE]).encode()
                iv = (hashlib.md5(self._shuffle(bytearray.fromhex(obs_key), bytearray.fromhex(aes_iv))).hexdigest()[:KEY_SIZE]).encode()
                result.append(CryptoCredential(key=key, iv=iv))

        self.keys = result
