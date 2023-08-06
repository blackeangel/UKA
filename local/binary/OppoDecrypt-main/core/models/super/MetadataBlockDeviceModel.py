import struct

from .MetadataBaseModel import MetadataBaseModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MetadataBlockDeviceModel(MetadataBaseModel):
    """
    Offset 0: First usable sector for allocating logical partitions. this will be
              the first sector after the initial geometry blocks, followed by the
              space consumed by metadata_max_size*metadata_slot_count*2.

    Offset 8: Alignment for defining partitions or partition extents. For example,
              an alignment of 1MiB will require that all partitions have a size evenly
              divisible by 1MiB, and that the smallest unit the partition can grow by is 1MiB.

              Alignment is normally determined at runtime when growing or adding
              partitions. If for some reason the alignment cannot be determined, then
              this predefined alignment in the geometry is used instead. By default it is set to 1MiB.

    Offset 12: Alignment offset for "stacked" devices. For example, if the "super"
               partition itself is not aligned within the parent block device's
               partition table, then we adjust for this in deciding where to place
               |first_logical_sector|.

               Similar to |alignment|, this will be derived from the operating system.
               If it cannot be determined, it is assumed to be 0.

    Offset 16: Block device size, as specified when the metadata was created.
               This can be used to verify the geometry against a target device.

    Offset 24: Partition name in the GPT. Any unused characters must be 0.

    Offset 60: Flags (see LP_BLOCK_DEVICE_* flags below).
    """

    _fmt = "<Q2IQ36sI"

    def __init__(self, buffer):
        (
            self.first_logical_sector,
            self.alignment,
            self.alignment_offset,
            self.block_device_size,
            self.partition_name,
            self.flags
        ) = struct.unpack(self._fmt, buffer[0:self.size])

        self.partition_name = self.partition_name.decode("utf-8").strip('\x00')
