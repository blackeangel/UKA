import argparse
import enum

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class EnumAction(argparse.Action):
    """
    Argparse action for handling Enums
    """

    def __init__(self, **kwargs):
        if (enum_type := kwargs.pop("type", None)) is None:
            raise ValueError("type must be assigned an Enum when using EnumAction")
        if not issubclass(enum_type, enum.Enum):
            raise TypeError("type must be an Enum when using EnumAction")

        super(EnumAction, self).__init__(**kwargs)

        self._enum = enum_type

    def __call__(self, parser, namespace, values, option_string=None):
        value = self._enum(values)
        setattr(namespace, self.dest, value)
