__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class MtkExtractorExceptions(Exception):
    ...


class MtkExtractorUnsupportedCryptoSettingsError(MtkExtractorExceptions):
    """Raised when not found crypto settings"""

    def __init__(self):
        self.message = f'Unsupported crypto settings'

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message