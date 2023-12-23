import dataclasses
import io
import shutil
import typing
from pathlib import Path
from typing import BinaryIO, Any

from InquirerPy.base import Choice

from cli import Cli
from core.decorators import ConfirmationExecution
from core.interfaces import ILogService
from core.models import PayloadModel
from core.models.super import MetadataHeaderModel, MetadataGeometryModel, MetadataPartitionModel, MetadataExtentModel, \
    MetadataPartitionGroupModel, MetadataBlockDeviceModel, MetadataTableDescriptorModel
from exceptions import SuperImgExtractorError
from extractors.BaseExtractor import BaseExtractor

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'

T = typing.TypeVar('T')

PARTITION_RESERVED_BYTES = 0x1000
METADATA_GEOMETRY_MAGIC = 0x616c4467
METADATA_GEOMETRY_SIZE = 0x1000
METADATA_HEADER_MAGIC = 0x414C5030
SECTOR_SIZE = 0x200

TARGET_TYPE_LINEAR = 0x0
TARGET_TYPE_ZERO = 0x1

PARTITION_ATTR_READONLY = (1 << 0)
PARTITION_ATTR_SLOT_SUFFIXED = (1 << 1)
PARTITION_ATTR_UPDATED = (1 << 2)
PARTITION_ATTR_DISABLED = (1 << 3)

BLOCK_DEVICE_SLOT_SUFFIXED = (1 << 0)
GROUP_SLOT_SUFFIXED = (1 << 0)


@dataclasses.dataclass
class _Metadata:
    header: MetadataHeaderModel = dataclasses.field(default=None)
    geometry: MetadataGeometryModel = dataclasses.field(default=None)
    partitions: list[MetadataPartitionModel] = dataclasses.field(default_factory=list)
    extents: list[MetadataExtentModel] = dataclasses.field(default_factory=list)
    groups: list[MetadataPartitionGroupModel] = dataclasses.field(default_factory=list)
    block_devices: list[MetadataBlockDeviceModel] = dataclasses.field(default_factory=list)

    @property
    def info(self) -> dict[Any, Any]:
        return self._get_info()

    @property
    def metadata_region(self) -> int:
        if self.geometry is None:
            return 0

        return PARTITION_RESERVED_BYTES + (METADATA_GEOMETRY_SIZE + self.geometry.metadata_max_size * self.geometry.metadata_slot_count) * 2

    def _get_info(self) -> dict[Any, Any]:
        return {}

    def get_offsets(self, slot_number: int = 0) -> list[int]:
        base = PARTITION_RESERVED_BYTES + (METADATA_GEOMETRY_SIZE * 2)
        _tmp_offset = self.geometry.metadata_max_size * slot_number
        primary_offset = base + _tmp_offset
        backup_offset = base + self.geometry.metadata_max_size * self.geometry.metadata_slot_count + _tmp_offset
        return [primary_offset, backup_offset]


class SuperImgExtractor(BaseExtractor):
    def __init__(self, logger: ILogService):
        self._metadata: _Metadata | None = None
        super().__init__(logger)

    @staticmethod
    def _get_data(fd: BinaryIO, count: int, size: int, clazz: T) -> list[T]:
        result = []
        while count > 0:
            result.append(clazz(fd.read(size)))
            count -= 1
        return result

    @staticmethod
    def _read_chunk(fd: BinaryIO, block_size):
        while True:
            data = fd.read(block_size)
            if not data:
                break
            yield data

    @staticmethod
    def _read_primary_geometry(fd: BinaryIO) -> MetadataGeometryModel:
        geometry = MetadataGeometryModel(fd.read(METADATA_GEOMETRY_SIZE))
        return geometry if geometry is not None else MetadataGeometryModel(fd.read(METADATA_GEOMETRY_SIZE))

    def _get_extent(self, partition: MetadataPartitionModel) -> list[tuple[int, int]]:
        parts = []
        for extent_number in range(partition.num_extents):
            index = partition.first_extent_index + extent_number
            extent = self._metadata.extents[index]

            if extent.target_type != TARGET_TYPE_LINEAR:
                raise SuperImgExtractorError(f"Unsupported target type in extent: {extent.target_type}")

            offset = extent.target_data * SECTOR_SIZE
            size = extent.num_sectors * SECTOR_SIZE
            parts.append((offset, size))

        return parts

    def _read_metadata_header(self, fd: BinaryIO, metadata: _Metadata):
        for index, offset in enumerate(offsets := metadata.get_offsets()):
            fd.seek(offset, io.SEEK_SET)
            header = MetadataHeaderModel(fd.read(typing.cast(int, MetadataHeaderModel.size)))
            for field in ["partitions", "extents", "groups", "block_devices"]:
                header.__setattr__(field, MetadataTableDescriptorModel(fd.read(typing.cast(int, MetadataTableDescriptorModel.size))))

            if header.magic != METADATA_HEADER_MAGIC:
                check_index = index + 1
                if check_index > len(offsets):
                    raise SuperImgExtractorError("Logical partition metadata has invalid magic value.")
                else:
                    self.logger.information(f"Read Backup header by offset 0x{offsets[check_index]:x}")
                    continue

            metadata.header = header
            fd.seek(offset + header.header_size, io.SEEK_SET)

    def _read_metadata(self, fd: BinaryIO) -> None:
        fd.seek(PARTITION_RESERVED_BYTES, io.SEEK_SET)
        metadata = _Metadata(geometry=self._read_primary_geometry(fd))

        if metadata.geometry.magic != METADATA_GEOMETRY_MAGIC:
            raise SuperImgExtractorError("Logical partition metadata has invalid geometry magic signature.")

        if metadata.geometry.metadata_slot_count == 0:
            raise SuperImgExtractorError("Logical partition metadata has invalid slot count.")

        if metadata.geometry.metadata_max_size % SECTOR_SIZE != 0:
            raise SuperImgExtractorError("Metadata max size is not sector-aligned.")

        self._read_metadata_header(fd, metadata)

        metadata.partitions = self._get_data(
            fd,
            metadata.header.partitions.num_entries,
            metadata.header.partitions.entry_size,
            MetadataPartitionModel
        )

        metadata.extents = self._get_data(
            fd,
            metadata.header.extents.num_entries,
            metadata.header.extents.entry_size,
            MetadataExtentModel
        )

        metadata.groups = self._get_data(
            fd,
            metadata.header.groups.num_entries,
            metadata.header.groups.entry_size,
            MetadataPartitionGroupModel
        )

        metadata.block_devices = self._get_data(
            fd,
            metadata.header.block_devices.num_entries,
            metadata.header.block_devices.entry_size,
            MetadataBlockDeviceModel
        )

        try:
            super_device: MetadataBlockDeviceModel = typing.cast(MetadataBlockDeviceModel, iter(metadata.block_devices).__next__())
            if metadata.metadata_region > super_device.first_logical_sector * SECTOR_SIZE:
                raise SuperImgExtractorError("Logical partition metadata overlaps with logical partition contents.")
        except StopIteration:
            raise SuperImgExtractorError("Metadata does not specify a super device.")

        self._metadata = metadata

    def _write_extent_to_file(self, in_fd: BinaryIO, out_fd: BinaryIO, offset: int, size: int):
        in_fd.seek(offset, io.SEEK_SET)

        for block in self._read_chunk(in_fd, self._metadata.geometry.logical_block_size):
            if size == 0:
                break

            out_fd.write(block)
            size -= self._metadata.geometry.logical_block_size

    def extract(self, fd: BinaryIO, output_dir: Path, file_size) -> PayloadModel:
        extract_files = []
        for partition in self._metadata.partitions:
            parts = []

            if partition.num_extents != 0:
                parts.extend(self._get_extent(partition))

            self.logger.information(f"Extracting partition {partition.name}")
            with open((out_path := output_dir / partition.filename), "wb") as out:
                for part in parts:
                    self._write_extent_to_file(fd, out, *part)

            extract_files.append(out_path)
        return PayloadModel(input_file=extract_files if extract_files else None, output_dir=output_dir)

    @ConfirmationExecution("Run extract partitions image from super partition?", forced=True)
    def run(self, payload: PayloadModel) -> PayloadModel:
        if payload.input_file is None:
            return payload

        if isinstance(payload.input_file, list):
            payload.input_file = payload.input_file[0]

        if (out_folder := payload.output_dir / "partitions").exists():
            shutil.rmtree(out_folder)

        out_folder.mkdir(parents=True, exist_ok=True)

        payload.output_dir = Cli.get_extract_folder(out_folder)

        try:
            with open(payload.input_file, 'rb') as fd:
                self._read_metadata(fd)

                if self._metadata.partitions is None:
                    raise SuperImgExtractorError("Partitions not found")

                choices = [Choice(value=self._metadata.partitions, name="All", enabled=True)]
                choices.extend([
                    Choice(
                        value=item,
                        name=item.name[:-2] if item.name.endswith(("_a", "_b")) else item.name,
                        enabled=False
                    ) for item in self._metadata.partitions if item.num_extents != 0])
                self._metadata.partitions = Cli.get_choice_extraction_partitions(choices)

                payload = self.extract(fd, payload.output_dir, payload.input_file.stat().st_size)
        except SuperImgExtractorError as error:
            self.logger.error(error.message)
        finally:
            return payload
