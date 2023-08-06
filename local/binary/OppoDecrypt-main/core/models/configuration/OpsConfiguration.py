import dataclasses
from .CryptoCredential import CryptoCredential

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


@dataclasses.dataclass
class OpsConfiguration:
    keys: dict[str, CryptoCredential]

    def __post_init__(self):
        d = dict()
        for key, value in self.keys.items():
            d.update({key: CryptoCredential(key=bytes.fromhex(value), iv=bytes())})

        self.keys = d
