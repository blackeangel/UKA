import struct

from .MetadataBaseModel import MetadataBaseModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataPartitionModel(MetadataBaseModel):
    """
    Offset 0: Name of this partition in ASCII characters. Any unused characters in
              the buffer must be set to 0. Characters may only be alphanumeric or _.
              The name must include at least one ASCII character, and it must be unique
              across all partition names. The length (36) is the same as the maximum
              length of a GPT partition name.
    Offset 36: Attributes for the partition (see LP_PARTITION_ATTR_* flags above).
    Offset 40: Index of the first extent owned by this partition. The extent will
               start at logical sector 0. Gaps between extents are not allowed.
    Offset 44: Number of extents in the partition. Every partition must have at least one extent.
    Offset 48: Group this partition belongs to.
    """

    _fmt = "<36s4I"

    def __init__(self, buffer: bytes) -> None:
        (
            self.name,
            self.attributes,
            self.first_extent_index,
            self.num_extents,
            self.group_index

        ) = struct.unpack(self._fmt, buffer[0:self.size])

        self.name = self.name.decode("utf-8").strip('\x00')

    @property
    def filename(self) -> str:
        return f'{self.name}.img'