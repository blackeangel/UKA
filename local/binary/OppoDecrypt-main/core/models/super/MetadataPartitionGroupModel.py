import struct

from .MetadataBaseModel import MetadataBaseModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataPartitionGroupModel(MetadataBaseModel):
    """
    Offset 0: Name of this group. Any unused characters must be 0.
    Offset 36: Flags (see LP_GROUP_*).
    Offset 40: Maximum size in bytes. If 0, the group has no maximum size.
    """

    _fmt = "<36sIQ"

    def __init__(self, buffer: bytes) -> None:
        (
            self.name,
            self.flags,
            self.maximum_size
        ) = struct.unpack(self._fmt, buffer[0:self.size])

        self.name = self.name.decode("utf-8").strip('\x00')
