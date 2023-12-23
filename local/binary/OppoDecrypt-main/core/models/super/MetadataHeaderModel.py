import dataclasses
import struct

from .MetadataBaseModel import MetadataBaseModel
from .MetadataTableDescriptorModel import MetadataTableDescriptorModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataHeaderModel(MetadataBaseModel):
    """
    +-----------------------------------------+
    | Header data - fixed size                |
    +-----------------------------------------+
    | Partition table - variable size         |
    +-----------------------------------------+
    | Partition table extents - variable size |
    +-----------------------------------------+

    Offset 0: Four bytes equal to `LP_METADATA_HEADER_MAGIC`
    Offset 4: Version number required to read this metadata. If the version is not
              equal to the library version, the metadata should be considered incompatible.
    Offset 6: Minor version. A library supporting newer features should be able to
              read metadata with an older minor version. However, an older library
              should not support reading metadata if its minor version is higher.
    Offset 8: The size of this header struct.
    Offset 12: SHA256 checksum of the header, up to |header_size| bytes, computed as if this field were set to 0.
    Offset 44: The total size of all tables. This size is contiguous; tables may not
               have gaps in between, and they immediately follow the header.
    Offset 48: SHA256 checksum of all table contents.
    Offset 80: Partition table descriptor.
    Offset 92: Extent table descriptor.
    Offset 104: Updatetable group descriptor.
    Offset 116: Block device table.
    Offset 128: Header flags are independent of the version number and intended to be informational only.
                New flags can be added without bumping the version.
    Offset 132: Reserved (zero), pad to 256 bytes.
    """

    _fmt = "<I2hI32sI32s"

    partitions: MetadataTableDescriptorModel = dataclasses.field(default=None)
    extents: MetadataTableDescriptorModel = dataclasses.field(default=None)
    groups: MetadataTableDescriptorModel = dataclasses.field(default=None)
    block_devices: MetadataTableDescriptorModel = dataclasses.field(default=None)

    def __init__(self, buffer: bytes) -> None:
        (
            self.magic,
            self.major_version,
            self.minor_version,
            self.header_size,
            self.header_checksum,
            self.tables_size,
            self.tables_checksum

        ) = struct.unpack(self._fmt, buffer[0:self.size])
        self.flags = 0
