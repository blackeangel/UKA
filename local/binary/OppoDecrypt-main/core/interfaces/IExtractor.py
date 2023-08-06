from __future__ import annotations

import abc
from pathlib import Path
from typing import BinaryIO, TypeVar

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'

T = TypeVar('T')


class IExtractor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def set_next_extractor(self, extractor: IExtractor) -> IExtractor:
        """Set next extractor of chain"""

    @abc.abstractmethod
    def extract(self, fd: BinaryIO, output_dir: Path, file_size) -> None:
        """Abstract method extract"""

    @abc.abstractmethod
    def run(self, payload: T) -> T:
        """Extractor run"""
