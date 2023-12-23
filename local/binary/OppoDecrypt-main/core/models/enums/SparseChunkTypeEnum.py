from enum import IntEnum

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class SparseChunkTypeEnum(IntEnum):
    CHUNK_TYPE_RAW = 0xCAC1
    CHUNK_TYPE_FILL = 0xCAC2
    CHUNK_TYPE_DONT_CARE = 0xCAC3
    CHUNK_TYPE_CRC32 = 0xCAC4

