__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class SuperImgExtractorExceptions(Exception):
    ...


class SuperImgExtractorError(SuperImgExtractorExceptions):
    """Raised any error unpacking"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
