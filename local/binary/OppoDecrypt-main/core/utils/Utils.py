import csv
import hashlib
import io
from pathlib import Path
from typing import BinaryIO, Callable

from InquirerPy.base import Choice

from core.models import CsvRecordModel
from core.models.enums.HashAlgorithmEnum import HashAlgorithmEnum
from exceptions import UtilsNoSupportedHashAlgorithmError, UtilsFileNotFoundError

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class Utils:
    @staticmethod
    def de_obfuscate_qualcomm(data, mask):
        def rol(x, n, bits=32):
            n = bits - n
            m = (2 ** n) - 1
            mask_bits = x & m
            return (x >> n) | (mask_bits << (bits - n))

        ret = bytearray()
        for i in range(0, len(data)):
            v = rol((data[i] ^ mask[i]), 4, 8)
            ret.append(v)
        return ret

    @staticmethod
    def mtk_header_shuffle(data, header_key=b"geyixue", header_size=0x6C) -> bytearray:
        key = bytearray(header_key)
        data = bytearray(data)
        for index in range(0, header_size):
            k = key[(index % len(key))]
            h = ((((data[index]) & 0xF0) >> 4) | (16 * ((data[index]) & 0xF)))
            data[index] = k ^ h

        return data

    @staticmethod
    def read_chunk(fd: BinaryIO, length: int, buffer_size=4096):
        if length < buffer_size:
            buffer_size = length

        while length > 0:
            chunk = fd.read(buffer_size)
            yield chunk

            length -= buffer_size

            if buffer_size > length:
                buffer_size = length

    @staticmethod
    def validate_checksum(checksum: str, dst: Path, algorithm: HashAlgorithmEnum, fill_func: Callable[[int], bytes] = None) -> bool:
        def hash_instance():
            match algorithm:
                case HashAlgorithmEnum.Md5:
                    _alg = hashlib.md5
                case HashAlgorithmEnum.Sha256:
                    _alg = hashlib.sha256
                case _:
                    raise UtilsNoSupportedHashAlgorithmError()
            return _alg()

        if not dst or not dst.exists():
            raise UtilsFileNotFoundError(dst)

        with open(dst, 'rb') as fd:
            for read_bytes in [0x40000, dst.stat().st_size]:
                alg = hash_instance()
                fd.seek(io.SEEK_SET)
                for chunk in Utils.read_chunk(fd, read_bytes):
                    alg.update(chunk)

                if fill_func and (fill := fill_func(dst.stat().st_size)):
                    alg.update(fill)

                if checksum == alg.hexdigest():
                    return True

        return False

    @staticmethod
    def parse_csv_file(csv_file_path: Path, input_files: list[Path]) -> list[Choice]:
        if csv_file_path.suffix.lower() != ".csv":
            raise AttributeError

        choices = []
        with open(csv_file_path, newline='') as fd:
            csv_reader = csv.DictReader(fd)
            for index, row in enumerate(csv_reader, start=1):
                record_model = CsvRecordModel(init_value=row)
                choices.append(
                    Choice(
                        value=[item for item in input_files if item.name in record_model.images],
                        name=f"{index}. [0x{record_model.id:02X}] {record_model.name}",
                        enabled=False
                    )
                )

        return choices

