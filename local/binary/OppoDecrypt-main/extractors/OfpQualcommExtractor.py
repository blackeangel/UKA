import dataclasses
import io
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import BinaryIO, Callable

from core.decorators import CheckOutputFolder
from core.interfaces import ILogService
from core.models import OfpQualcommConfiguration, HashAlgorithmEnum, PayloadModel
from core.utils import Crypto, Utils
from exceptions import QualcommExtractorXMLSectionNotFoundError, QualcommExtractorUnsupportedCryptoSettingsError, \
    UtilsNoSupportedHashAlgorithmError, UtilsFileNotFoundError
from .BaseExtractor import BaseExtractor

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'
__all__ = ["OfpQualcommExtractor"]

CHUNK_SIZE = 0x1000
XML_MAGIC = 0x7CEF
XML_MAGIC_OFFSETS = [0x200, 0x1000]


@dataclasses.dataclass
class Payload:
    sha256: str = None
    md5: str = None
    filename: str = None
    start_position: int = -1
    length: int = 0
    rlength: int = 0
    decrypt_size = 0x40000


@dataclasses.dataclass
class Job:
    payload: Payload = None
    action: Callable = None


class OfpQualcommExtractor(BaseExtractor):
    def __init__(self, configuration: dict[str, any], logger: ILogService):
        super().__init__(logger)
        self._configuration = OfpQualcommConfiguration(**configuration)
        self._pagesize = None

    def _copy(self, fd: BinaryIO, output_dir: Path, payload: Payload) -> Path:
        self.logger.information(f"Extracting {payload.filename}")
        fd.seek(payload.start_position)
        with open((dst_file := output_dir / payload.filename), 'wb') as out:
            for chunk in Utils.read_chunk(fd, payload.length, buffer_size=CHUNK_SIZE):
                out.write(chunk)

        return dst_file

    def _decrypt_file(self, fd: BinaryIO, output_dir: Path, payload: Payload) -> Path:
        self.logger.information(f"Extracting {payload.filename}")
        if payload.rlength == payload.length:
            _ = payload.length
            payload.length = (payload.length // 0x4 * 0x4)

            if _ % 0x4 != 0:
                payload.length += 0x4

        fd.seek(payload.start_position)
        with open((dst_file := output_dir / payload.filename), 'wb') as out:
            size = payload.decrypt_size
            if payload.rlength < payload.decrypt_size:
                size = payload.rlength

            crypto_data = fd.read(size)
            if size % 4:
                crypto_data += (4 - (size % 4)) * b'\x00'

            data = Crypto.decrypt_aes_cfb(self._crypto_config, crypto_data)
            out.write(data[:size])

            if payload.rlength > payload.decrypt_size:
                fd.seek(payload.start_position + size)
                length = payload.rlength - size

                while length > 0:
                    size_sub = length if length < 0x100000 else 0x100000
                    out.write(fd.read(size_sub))
                    length -= size_sub

            if payload.rlength % 0x1000 != 0:
                fill = bytearray([0x00 for i in range(0x1000 - (payload.rlength % 0x1000))])

        return dst_file

    def _decrypt_xml_data(self, xml_crypto_data: bytes) -> str:
        for version, crypto_credential in self._configuration.keys.items():
            self.logger.trace(f"Check {version}")
            if b"<?xml" in (result := Crypto.decrypt_aes_cfb(crypto_credential, xml_crypto_data)):
                self._crypto_config = crypto_credential
                return result[:result.rfind(b">") + 1].decode('utf-8')

        raise QualcommExtractorUnsupportedCryptoSettingsError()

    def _find_xml_crypto_data(self, fd: BinaryIO, file_size: int):
        fd.seek(io.SEEK_SET)
        for xml_magic_offset in XML_MAGIC_OFFSETS:
            fd.seek(file_size - xml_magic_offset + 0x10, io.SEEK_SET)

            if struct.unpack("<I", fd.read(4))[0] == XML_MAGIC:
                self._pagesize = xml_magic_offset
                break

        if not self._pagesize:
            raise QualcommExtractorXMLSectionNotFoundError(fd.name)

        xml_offset = file_size - self._pagesize
        fd.seek(xml_offset + 0x14)
        offset = struct.unpack("<I", fd.read(4))[0] * self._pagesize
        length = struct.unpack("<I", fd.read(4))[0]

        if length < 200:  # A57 hack
            length = xml_offset - offset - 0x57
        fd.seek(offset)

        return fd.read(length)

    def _parse_xml_item(self, element: ET.Element) -> Payload:
        payload = Payload()

        if value := element.attrib.get('Path', None):
            payload.filename = value
        elif value := element.attrib.get('filename', None):
            payload.filename = value

        payload.sha256 = element.attrib.get('sha256', None)
        payload.md5 = element.attrib.get('md5', None)

        if value := element.attrib.get('FileOffsetInSrc', None):
            payload.start_position = int(value) * self._pagesize
        elif value := element.attrib.get('SizeInSectorInSrc', None):
            payload.start_position = int(value) * self._pagesize

        if value := element.attrib.get('SizeInByteInSrc', None):
            payload.rlength = int(value)

        payload.length = int(value) * self._pagesize if (value := element.attrib.get('SizeInSectorInSrc', None)) else payload.rlength

        return payload

    def _parse_xml_section(self, xml_data: str) -> list[Job]:
        result: list[Job] = list()
        root = ET.fromstring(xml_data)
        for child in root:
            for item in child:
                if "Path" not in item.attrib and "filename" not in item.attrib:
                    for sub_item in item:
                        payload = self._parse_xml_item(sub_item)

                        if not payload.filename or payload.start_position == -1:
                            continue

                        result.append(Job(payload=payload, action=self._decrypt_file))

                payload = self._parse_xml_item(item)
                if not payload.filename or payload.start_position == -1:
                    continue

                match child.tag:
                    case "Sahara":
                        payload.decrypt_size = payload.rlength
                    case "Config" | "Provision" | "ChainedTableOfDigests" | "DigestsToSign" | "Firmware":
                        payload.length = payload.rlength

                if child.tag in ["DigestsToSign", "ChainedTableOfDigests", "Firmware"]:
                    action = self._copy
                else:
                    action = self._decrypt_file

                result.append(Job(payload=payload, action=action))

        return result

    @CheckOutputFolder
    def extract(self, fd: BinaryIO, output_dir: Path, file_size) -> PayloadModel:
        xml_data = self._decrypt_xml_data(self._find_xml_crypto_data(fd, file_size))

        (pro_file_path := output_dir / "ProFile.xml").write_text(xml_data)
        self.logger.debug(f"Save Profile in {pro_file_path}")

        for job in self._parse_xml_section(xml_data):
            dst_path = job.action(fd, output_dir, job.payload)

            if job.payload.md5 and job.payload.md5 != "":
                algorithm = HashAlgorithmEnum.Md5
            elif job.payload.sha256 and job.payload.sha256 != "":
                algorithm = HashAlgorithmEnum.Sha256
            else:
                self.logger.debug(f"Skip check checksum for {job.payload.filename}")
                continue

            try:
                if Utils.validate_checksum(job.payload.__getattribute__(algorithm), dst_path, algorithm):
                    self.logger.debug(f"Check {job.payload.filename} success! Algorithm {algorithm}: verified")
                else:
                    self.logger.error(f"{dst_path} hashes error. File might be broken!")
            except UtilsNoSupportedHashAlgorithmError as error:
                self.logger.error(error.message)

            except UtilsFileNotFoundError as error:
                self.logger.error(error.message)

        return PayloadModel(output_dir=output_dir)

    def run(self, payload: PayloadModel) -> PayloadModel:
        self.logger.information("Run Qualcomm extractor")

        return super().run(payload)
