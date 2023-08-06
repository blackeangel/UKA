import dataclasses

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


@dataclasses.dataclass
class CryptoCredential:
    key: bytes
    iv: bytes
