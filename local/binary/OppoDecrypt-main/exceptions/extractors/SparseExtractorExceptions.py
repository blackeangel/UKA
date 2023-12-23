__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class SparseExtractorExceptions(Exception):
    ...


class SparseExtractorNotSparseImageError(SparseExtractorExceptions):
    """Raised when image not sparse"""

    def __init__(self, input_file):
        self.message = f'{input_file} not sparse image'

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message
