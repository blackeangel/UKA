from __future__ import annotations

import abc
from pathlib import Path
from typing import BinaryIO

from core.interfaces import IExtractor, ILogService
from core.models import CryptoCredential, PayloadModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class BaseExtractor(IExtractor):
    _next_extractor: IExtractor = None

    def __init__(self, logger: ILogService):
        self.crypto_config: CryptoCredential | None = None
        self.logger = logger

    @property
    def next_extractor(self) -> IExtractor:
        return self._next_extractor

    @next_extractor.setter
    def next_extractor(self, extractors: list[BaseExtractor]):
        self._next_extractor = extractors.pop(0)

        _next_extractor = self._next_extractor
        for extractor in extractors:
            _next_extractor = _next_extractor.set_next_extractor(extractor)

    def set_next_extractor(self, extractor: IExtractor) -> IExtractor:
        self._next_extractor = extractor

        return extractor

    def add_first_extractor(self, extractor: IExtractor):
        extractors = []
        first_extractor = self._next_extractor
        while True:
            if not first_extractor:
                break

            extractors.append(first_extractor)
            first_extractor = first_extractor.next_extractor

        list(map(lambda x: x.set_next_extractor(None), extractors))

        _next_extractor = extractor
        for _ in extractors:
            _next_extractor = _next_extractor.set_next_extractor(_)

        return self.set_next_extractor(extractor)

    @abc.abstractmethod
    def extract(self, fd: BinaryIO, output_dir: Path, file_size) -> PayloadModel:
        ...

    @abc.abstractmethod
    def run(self, payload: PayloadModel) -> PayloadModel:
        file_size = payload.input_file.stat().st_size
        with open(payload.input_file, 'rb') as fd:
            payload = self.extract(fd, payload.output_dir, file_size)

        if self.next_extractor:
            return self._next_extractor.run(payload)

        return payload
