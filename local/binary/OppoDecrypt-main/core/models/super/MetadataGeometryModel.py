import struct

from .MetadataBaseModel import MetadataBaseModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataGeometryModel(MetadataBaseModel):
    """
    Offset 0: Magic signature
    Offset 4: Size of the `MetadataGeometryModel`
    Offset 8: SHA256 checksum
    Offset 40: Maximum amount of space a single copy of the metadata can use
    Offset 44: Number of copies of the metadata to keep
    Offset 48: Logical block size
    """
    _fmt = "<2I32s3I"

    def __init__(self, buffer: bytes) -> None:
        (
            self.magic,
            self.struct_size,
            self.checksum,
            self.metadata_max_size,
            self.metadata_slot_count,
            self.logical_block_size

        ) = struct.unpack(self._fmt, buffer[0:self.size])
