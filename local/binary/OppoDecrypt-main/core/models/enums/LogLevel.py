from enum import Flag, auto

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class LogLevel(Flag):
    Trace = auto()
    Debug = auto()
    Info = auto()
    Warning = auto()
    Error = auto()
    Critical = auto()
