import argparse
from pathlib import Path

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class ExtensionsAction(argparse.Action):
    """
    Argparse action for check file extensions
    """
    def __init__(self, extensions: list[str], *args, **kwargs):
        self._extensions = extensions

        super(ExtensionsAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values: Path, option_string=None):
        if values.suffix[1:] not in self._extensions:
            parser.error(f"file doesn't end with one of [{self._extensions}]")
        else:
            setattr(namespace, self.dest, values)
