import struct

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataBaseModel:
    _fmt = None

    @classmethod
    @property
    def size(cls) -> int:
        return struct.calcsize(cls._fmt)
