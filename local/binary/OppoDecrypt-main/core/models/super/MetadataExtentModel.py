import struct

from .MetadataBaseModel import MetadataBaseModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataExtentModel(MetadataBaseModel):
    """
    Offset 0: Length of this extent, in 512-byte sectors.
    Offset 8: Target type for device-mapper (see LP_TARGET_TYPE_* values).
    Offset 12: Contents depends on target_type. LINEAR: The sector on the physical partition that this extent maps onto.
               ZERO: This field must be 0.
    Offset 20: Contents depends on target_type. LINEAR: Must be an index into the block devices table.
    """

    _fmt = "<QIQI"

    def __init__(self, buffer: bytes) -> None:
        (
            self.num_sectors,
            self.target_type,
            self.target_data,
            self.target_source

        ) = struct.unpack(self._fmt, buffer[0:struct.calcsize(self._fmt)])
