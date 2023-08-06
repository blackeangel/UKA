import dataclasses
import hashlib

from core.utils.Utils import Utils
from .CryptoCredential import CryptoCredential

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


@dataclasses.dataclass
class OfpQualcommConfiguration:
    keys: dict[str, CryptoCredential]

    def __post_init__(self):
        d = dict()
        for key, value in self.keys.items():
            mc = bytearray.fromhex(value.get('Mc', ''))
            user_key = bytearray.fromhex(value.get('UserKey', ''))
            ivec = bytearray.fromhex(value.get('Ivec', ''))

            k = (hashlib.md5(Utils.de_obfuscate_qualcomm(user_key, mc)).hexdigest()[0:16]).encode()
            iv = (hashlib.md5(Utils.de_obfuscate_qualcomm(ivec, mc)).hexdigest()[0:16]).encode()

            d.update({key: CryptoCredential(key=k, iv=iv)})

        self.keys = d

