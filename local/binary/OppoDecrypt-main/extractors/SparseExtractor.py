import dataclasses
import io
import struct
from pathlib import Path
from typing import BinaryIO

from cli import Cli
from core.decorators import ConfirmationExecution
from core.interfaces import ILogService
from core.models import SparseChunkTypeEnum, PayloadModel
from core.utils import Utils
from exceptions import SparseExtractorNotSparseImageError
from extractors.BaseExtractor import BaseExtractor

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'
__all__ = ["SparseExtractor"]


@dataclasses.dataclass
class _SparseHeader:
    def __init__(self, buffer):
        fmt = '<I4H4I'
        (
            self.magic,              # 0xed26ff3a
            self.major_version,      # (0x1) - reject images with higher major versions
            self.minor_version,      # (0x0) - allow images with higer minor versions
            self.file_header_size,   # 28 bytes for first revision of the file format
            self.chunk_header_size,  # 12 bytes for first revision of the file format
            self.block_size,         # block size in bytes, must be a multiple of 4 (4096)
            self.total_blocks,       # total blocks in the non-sparse output image
            self.total_chunks,       # total chunks in the sparse input image
            self.image_checksum      # CRC32 checksum of the original data, counting "don't care"
        ) = struct.unpack(fmt, buffer[0:struct.calcsize(fmt)])


@dataclasses.dataclass
class _SparseChunkHeader:
    """
        Following a Raw or Fill or CRC32 chunk is data.
        For a Raw chunk, it's the data in chunk_sz * blk_sz.
        For a Fill chunk, it's 4 bytes of the fill data.
        For a CRC32 chunk, it's 4 bytes of CRC32
     """
    def __init__(self, buffer, header: _SparseHeader):
        fmt = '<2H2I'
        (
            self.chunk_type,        # 0xCAC1 -> raw; 0xCAC2 -> fill; 0xCAC3 -> don't care */
            self._reserved,
            self.chunk_size,          # in blocks in output image * /
            self.total_size,          # in bytes of chunk input file including chunk header and data * /
        ) = struct.unpack(fmt, buffer[0:struct.calcsize(fmt)])

        self._header = header

    @property
    def data_size(self):
        return self.total_size - self._header.chunk_header_size

    @property
    def sector_size(self):
        return (self.chunk_size * self._header.block_size) >> 9


class SparseExtractor(BaseExtractor):
    _SPARSE_HEADER_MAGIC = 0xED26FF3A
    _SPARSE_HEADER_SIZE = 0x1C
    _SPARSE_CHUNK_HEADER_SIZE = 0xC
    _BUFFER_PAGE_SIZE = 0x1000

    def __init__(self, logger: ILogService):
        self._out_filename: str = "super.unsparse.img"
        super().__init__(logger)

    def _unsparse(self, in_fd: BinaryIO, out_fd: BinaryIO, header: _SparseHeader):
        chunks = header.total_chunks
        in_fd.seek(header.file_header_size - self._SPARSE_HEADER_SIZE, io.SEEK_CUR)

        while chunks > 0:
            chunk_header = _SparseChunkHeader(in_fd.read(self._SPARSE_CHUNK_HEADER_SIZE), header)

            match chunk_header.chunk_type:
                case SparseChunkTypeEnum.CHUNK_TYPE_RAW:
                    if header.chunk_header_size > self._SPARSE_CHUNK_HEADER_SIZE:
                        in_fd.seek(header.chunk_header_size - self._SPARSE_CHUNK_HEADER_SIZE, 1)
                    data = in_fd.read(chunk_header.data_size)
                    if len(data) == chunk_header.sector_size << 0x9:
                        out_fd.write(data)

                case SparseChunkTypeEnum.CHUNK_TYPE_FILL:
                    if header.chunk_header_size > self._SPARSE_CHUNK_HEADER_SIZE:
                        in_fd.seek(header.chunk_header_size - self._SPARSE_CHUNK_HEADER_SIZE, 1)
                    in_fd.seek(chunk_header.data_size, io.SEEK_CUR)
                    out_fd.write(struct.pack("B", 0) * (chunk_header.sector_size << 0x9))

                case SparseChunkTypeEnum.CHUNK_TYPE_DONT_CARE:
                    out_fd.seek(chunk_header.sector_size << 0x9, io.SEEK_CUR)

                case _:
                    out_fd.write(struct.pack("B", 0) * (chunk_header.sector_size << 0x9))

            chunks -= 1

    def is_sparse(self, fd: BinaryIO) -> bool:
        current_position = fd.tell()
        fd.seek(0, io.SEEK_SET)

        _fmt = '<I'
        (
            magic_number,
        ) = struct.unpack(_fmt, fd.read(struct.calcsize(_fmt)))

        fd.seek(current_position)

        return magic_number == self._SPARSE_HEADER_MAGIC

    def extract(self, fd: BinaryIO, output_dir: Path, file_size) -> PayloadModel:
        if not self.is_sparse(fd):
            raise SparseExtractorNotSparseImageError(fd.name)

        header = _SparseHeader(fd.read(self._SPARSE_HEADER_SIZE))
        if not (input_file := Path(fd.name)).name.startswith("super"):
            self._out_filename = f"{input_file.stem}.unsparse{input_file.suffix}"

        with open((dst_path := output_dir / self._out_filename), "rb+" if dst_path.exists() else "wb", buffering=self._BUFFER_PAGE_SIZE) as out:
            self._unsparse(fd, out, header)
            out.truncate()
            out.flush()

        return PayloadModel(input_file=dst_path, output_dir=output_dir)

    @ConfirmationExecution("Run conversion to non sparse image?")
    def run(self, payload: PayloadModel) -> PayloadModel:
        if isinstance(payload.input_file, Path) and not payload.input_file.exists():
            raise FileNotFoundError

        elif isinstance(payload.input_file, Path) and payload.input_file.exists():
            payload.input_file = [payload.input_file]

        elif isinstance(payload.input_file, list) and len(payload.input_file) > 0:
            for path in payload.input_file:
                if not path.exists():
                    raise FileNotFoundError

        elif payload.input_file is None:
            find_images = list(filter(lambda x: x.name != self._out_filename, list(payload.output_dir.glob(payload.search_pattern))))
            if len(find_images) == 0:
                raise FileNotFoundError

            if len(find_images) == 1:
                payload.input_file = find_images
            else:
                self.logger.information(f"Multiple files found")
                csv_path = Cli.get_super_map_path(find_images)
                choices = Utils.parse_csv_file(csv_path, find_images)
                payload.input_file = Cli.get_choice_build_configuration(choices)
        else:
            raise AttributeError
        self.logger.information("Run sparse extractor")

        try:
            for input_file in payload.input_file:
                self.logger.debug(f"Convert {input_file} to non sparse image")

                with open(input_file, "rb") as fd:
                    result = self.extract(fd, payload.output_dir, input_file.stat().st_size)

            out_file = result.input_file.parent / f"{result.input_file.name.replace('.unsparse', '')}"
            if out_file.exists():
                out_file.unlink(missing_ok=True)

            payload.input_file = [result.input_file.rename(out_file)]

            self.logger.information(f"Extract successfully")

        except SparseExtractorNotSparseImageError as error:
            self.logger.error(error.message)
        finally:
            payload.input_file = payload.input_file.pop(0)

            if self.next_extractor:
                return self._next_extractor.run(payload)

            return payload

