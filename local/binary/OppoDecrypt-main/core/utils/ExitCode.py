try:
    from enum import IntEnum as Base
except ImportError:
    Base = object

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class ExitCode(Base):
    """
    Exit status codes.
        OK           Successful termination
        USAGE        Command-line usage error
        DATA_ERR     Invalid data
        NO_INPUT     No input provided
        NO_USER      User unknown
        NO_HOST      Hostname unknown
        UNAVAILABLE  Service unavailable
        SOFTWARE     Internal software error
        OS_ERR       System error (e.g., can't fork)
        OS_FILE      File missing
        CANT_CREATE  Can't create (user) output file
        IO_ERR       Input/output error
        TEMP_FAIL    A temporary failure; the user is invited to retry
        PROTOCOL     A protocol error
        NO_PERM      Permission denied
        CONFIG       Configuration error
    """

    """Successful termination"""
    OK = 0

    """Command-line usage error"""
    USAGE = 64

    """Invalid data"""
    DATA_ERR = 65

    """No input provided"""
    NO_INPUT = 66

    """User unknown"""
    NO_USER = 67

    """Hostname unknown"""
    NO_HOST = 68

    """Service unavailable"""
    UNAVAILABLE = 69

    """Internal software error"""
    SOFTWARE = 70

    """System error (e.g., can't fork)"""
    OS_ERR = 71

    """File missing"""
    OS_FILE = 72

    """Can't create (user) output file"""
    CANT_CREATE = 73

    """Input/output error"""
    IO_ERR = 74

    """A temporary failure; the user is invited to retry"""
    TEMP_FAIL = 75

    """A protocol error"""
    PROTOCOL = 76

    """Permission denied"""
    NO_PERM = 77

    """Configuration error"""
    CONFIG = 78
