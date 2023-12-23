from pathlib import Path

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class UtilsError(Exception):
    ...


class UtilsNoSupportedHashAlgorithmError(UtilsError):
    """Raised when not supported hash algorithm"""

    def __init__(self):
        self.message = f"Not supported algorithm"

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message


class UtilsFileNotFoundError(UtilsError):
    """Raised when not file found"""

    def __init__(self, path: str | Path):
        self.message = f"File {path} not found"

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message
