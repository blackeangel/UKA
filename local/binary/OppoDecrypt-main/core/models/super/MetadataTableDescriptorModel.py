import struct

from .MetadataBaseModel import MetadataBaseModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataTableDescriptorModel(MetadataBaseModel):
    """
    Offset 0: Location of the table, relative to end of the metadata header.
    Offset 4: Number of entries in the table.
    Offset 8: Size of each entry in the table, in bytes.
    """
    _fmt = "<3I"

    def __init__(self, buffer: bytes) -> None:
        (
            self.offset,
            self.num_entries,
            self.entry_size

        ) = struct.unpack(self._fmt, buffer[:self.size])
