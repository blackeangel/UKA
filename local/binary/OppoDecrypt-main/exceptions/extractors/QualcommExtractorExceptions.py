__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class QualcommExtractorError(Exception):
    ...


class QualcommExtractorXMLSectionNotFoundError(QualcommExtractorError):
    """Raised when not found xml section"""

    def __init__(self, file_path: str):
        self.message = f'Not found xml section in {file_path}'

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message


class QualcommExtractorUnsupportedCryptoSettingsError(QualcommExtractorError):
    """Raised when not found crypto settings"""

    def __init__(self):
        self.message = f'Unsupported crypto settings'

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message