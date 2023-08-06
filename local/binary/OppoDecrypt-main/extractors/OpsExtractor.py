import dataclasses
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import BinaryIO, Tuple, Callable

from core.decorators import CheckOutputFolder
from core.interfaces import ILogService
from core.models import CryptoCredential, HashAlgorithmEnum, OpsConfiguration, PayloadModel
from core.utils import Crypto, Utils
from exceptions import OpsExtractorUnsupportedCryptoSettingsError, UtilsNoSupportedHashAlgorithmError, UtilsFileNotFoundError
from .BaseExtractor import BaseExtractor

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'
__all__  = ["OpsExtractor"]

CHUNK_SIZE = 0x1000
HEADER_OFFSET = 0x200
HEADER_SIZE = 0x200


@dataclasses.dataclass
class _Payload:
    sha256: str = None
    filename: str = None
    start_position: int = -1
    length: int = 0
    rlength: int = 0
    sparse: bool = False


@dataclasses.dataclass
class _Job:
    payload: _Payload = None
    action: Callable = None


class OpsExtractor(BaseExtractor):
    _KEY = struct.unpack("<4I", bytes.fromhex("d1b5e39e5eea049d671dd5abd2afcbaf"))

    def __init__(self, configuration: dict[str, any], logger: ILogService):
        self._configuration = OpsConfiguration(**configuration)
        super().__init__(logger)

    @staticmethod
    def _find_xml_crypto_data(fd: BinaryIO, file_size: int) -> Tuple[bytes, int]:
        fd.seek(file_size - HEADER_OFFSET)
        hdr = fd.read(HEADER_SIZE)
        xml_length = struct.unpack('<I', hdr[0x18:0x18 + 4])[0]
        fd.seek(file_size - HEADER_SIZE - (xml_length + (HEADER_SIZE - (xml_length % HEADER_SIZE))))
        return fd.read(xml_length + (HEADER_SIZE - (xml_length % HEADER_SIZE))), xml_length

    @staticmethod
    def _parse_xml_item(element: ET.Element) -> _Payload:
        payload = _Payload()

        if value := element.attrib.get('Path', None):
            payload.filename = value
        elif value := element.attrib.get('filename', None):
            payload.filename = value

        payload.sha256 = element.attrib.get('Sha256', None)

        if value := element.attrib.get('FileOffsetInSrc', None):
            payload.start_position = int(value) * HEADER_OFFSET

        if value := element.attrib.get('SizeInByteInSrc', None):
            payload.rlength = int(value)

        if value := element.attrib.get('sparse', None):
            payload.sparse = True if value.lower() == "true" else False

        payload.length = int(value) * HEADER_OFFSET if (value := element.attrib.get('SizeInSectorInSrc', None)) else payload.rlength

        return payload

    def _digest_fill(self, file_size: int) -> bytes:
        if file_size % 0x1000 > 0:
            fill_size = 0x1000 - (file_size % 0x1000)
            return struct.pack(f"<{fill_size}B", *([0] * fill_size))

    def _copy(self, fd: BinaryIO, output_dir: Path, payload: _Payload) -> Path:
        self.logger.information(f"Extracting {payload.filename}")
        fd.seek(payload.start_position)
        with open((dst_file := output_dir / payload.filename), 'wb') as out:
            for chunk in Utils.read_chunk(fd, payload.length, buffer_size=CHUNK_SIZE):
                out.write(chunk)

        return dst_file

    def _decrypt_file(self, fd: BinaryIO, output_dir: Path, payload: _Payload) -> Path:
        self.logger.information(f"Extracting {payload.filename}")
        fd.seek(payload.start_position)
        crypto_data = fd.read(payload.length)
        if payload.length % 4:
            fill_count = (4 - (payload.length % 4))
            crypto_data += struct.pack(f"<{fill_count}B", *([0] * fill_count))

        data = self._decrypt(crypto_data, self.crypto_config)
        with open((dst_file := output_dir / payload.filename), 'wb') as out:
            out.write(data[:payload.length])

        return dst_file

    def _decrypt(self, crypto_data, crypto_config: CryptoCredential):
        out = bytearray()
        crypto_data = bytearray(crypto_data)
        length = len(crypto_data)
        custom_key = self._KEY
        mbox = struct.unpack("62B", crypto_config.key)
        if length > 0xF:
            for ptr in range(0, length, 0x10):
                custom_key = Crypto.ops_key_update(custom_key, mbox)
                data = struct.unpack("<4I", crypto_data[ptr:ptr + 0x10])
                out.extend(struct.pack("<4I", *[custom_key[index] ^ data[index] for index in range(0, 4)]))
                custom_key = data
                length = length - 0x10

        return out

    def _decrypt_xml_data(self, xml_crypto_data: bytes, xml_length: int) -> str:
        for version, crypto_config in self._configuration.keys.items():
            self.logger.trace(f"Check {version}")
            if b"<?xml" in (result := self._decrypt(xml_crypto_data, crypto_config)):
                self.crypto_config = crypto_config
                return ''.join(filter(str.isascii, result[:xml_length].decode('utf-8')))

        raise OpsExtractorUnsupportedCryptoSettingsError

    def _parse_xml_section(self, xml_data: str):
        result: list[_Job] = list()
        root = ET.fromstring(xml_data)
        for child in root:
            for item in child:
                if "Path" not in item.attrib and "filename" not in item.attrib:
                    for sub_item in item:
                        payload = self._parse_xml_item(sub_item)

                        if not payload.filename or payload.start_position == -1:
                            continue

                        result.append(_Job(payload=payload, action=self._copy))

                payload = self._parse_xml_item(item)

                if not payload.filename or payload.start_position == -1:
                    continue

                if child.tag in ["SAHARA"]:
                    action = self._decrypt_file
                else:
                    action = self._copy

                result.append(_Job(payload=payload, action=action))

        return result

    @CheckOutputFolder
    def extract(self, fd: BinaryIO, output_dir: Path, file_size):
        xml_data = self._decrypt_xml_data(*self._find_xml_crypto_data(fd, file_size))

        (pro_file_path := output_dir / "settings.xml").write_text(xml_data)
        self.logger.debug(f"Save settings.xml in {pro_file_path}")

        jobs = self._parse_xml_section(xml_data)
        for index, job in enumerate(jobs):
            dst_path = job.action(fd, output_dir, job.payload)

            if job.payload.sha256 and job.payload.sha256 != "" and not job.payload.sparse:
                algorithm = HashAlgorithmEnum.Sha256
            else:
                self.logger.debug(f"Skip check checksum for {job.payload.filename}")
                continue

            try:
                if Utils.validate_checksum(job.payload.__getattribute__(algorithm), dst_path, algorithm, fill_func=self._digest_fill):
                    self.logger.debug(f"Check {job.payload.filename} success! Algorithm {algorithm}: verified")
                else:
                    self.logger.error(f"{dst_path} hashes error. File might be broken!")
            except UtilsNoSupportedHashAlgorithmError as error:
                self.logger.error(error.message)

            except UtilsFileNotFoundError as error:
                self.logger.error(error.message)

        return PayloadModel(output_dir=output_dir)

    def run(self, payload: PayloadModel) -> PayloadModel:
        self.logger.information("Run OPS extractor")

        return super().run(payload)

