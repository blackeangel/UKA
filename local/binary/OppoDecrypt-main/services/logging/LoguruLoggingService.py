from typing import Any

from loguru import logger

from core.interfaces import ILogService
from core.models import LogLevel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class LoguruLoggingService(ILogService):
    def __init__(self, configuration: dict[Any: Any]):
        self._logger_id = logger.configure(**configuration)

    @classmethod
    def log(cls, level: LogLevel, message: str, exception: Exception = None):
        match level:
            case LogLevel.Critical:
                logger.critical(message)
            case LogLevel.Debug:
                logger.debug(message)
            case LogLevel.Error:
                logger.error(message)
            case LogLevel.Info:
                logger.info(message)
            case LogLevel.Trace:
                logger.trace(message)
            case LogLevel.Warning:
                logger.warning(message)

