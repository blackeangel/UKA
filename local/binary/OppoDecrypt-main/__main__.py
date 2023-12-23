import sys
from typing import Any

import yaml
from pathlib import Path
import argparse

from core.interfaces import IBaseExtractService
from core.utils import ExitCode
from core.actions import EnumAction, ExtensionsAction
from core.models import CpuSupportEnum
from dependency_injector.wiring import inject, Provide
from containers import ApplicationContainer

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'
__version__ = '1.0.0'


def load_yaml_configuration() -> dict:
    def run_func(loader, node):
        value = loader.construct_scalar(node)
        if '.' in value:
            module_name, fun_name = value.rsplit('.', 1)
        else:
            module_name = '__main__'
            fun_name = value

        try:
            __import__(module_name)
        except ImportError as exc:
            raise

        module = sys.modules[module_name]
        fun = getattr(module, fun_name)

        try:
            return fun()
        except TypeError:
            return fun

    yaml.add_constructor('!func', run_func)

    with open(Path(Path(__file__).resolve().parent / 'config.yml'), 'r') as stream:
        return yaml.full_load(stream)


def set_debug_mode(handlers: dict[Any, Any]) -> dict[Any, Any]:
    for item in configuration['log']['handlers']:
        item.update({'level': 'DEBUG', 'format': '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> ' + item['format']})

    return handlers


@inject
def main(service: IBaseExtractService = Provide[ApplicationContainer.extract_service], **kwargs) -> None:
    service.extract(**kwargs)


def create_parser() -> argparse.ArgumentParser:
    _parser = argparse.ArgumentParser(
        prog="OppoDecrypt",
        description=f"OppoDecrypt - command-line tool for extracting partition images from .ofp or .ops"
    )

    _parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"OppoDecrypt version [{__version__}]"
    )

    _parser.add_argument(
        "-c",
        "--cpu",
        required=True,
        help=f"choices, { (choices := tuple(v.value for k, v in CpuSupportEnum.__members__.items()))}",
        dest="cpu",
        type=CpuSupportEnum,
        choices=choices,
        action=EnumAction
    )

    _parser.add_argument(
        "--debug",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction
    )

    _parser.add_argument(
        "--sparse",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction
    )

    _parser.add_argument(
        "INPUT_FILE",
        type=Path,
        action=ExtensionsAction,
        extensions=["ofp", "ops"],
        nargs="?",
    )
    _parser.add_argument(
        "OUTPUT_DIR",
        type=Path,
        nargs="?",
    )

    return _parser


if __name__ == '__main__':
    parser = create_parser()
    namespace = parser.parse_args()

    if len(sys.argv) >= 2:
        if not namespace.INPUT_FILE.exists():
            sys.stderr.write(f"File `{namespace.INPUT_FILE}` not found\n\n")
            parser.print_help(file=sys.stderr)
            sys.exit(ExitCode.CONFIG)

        container = ApplicationContainer()
        configuration = load_yaml_configuration()
        debug = vars(namespace).pop('debug', False)
        if debug:
            configuration['log']['handlers'] = set_debug_mode(configuration['log']['handlers'])

        container.configuration.from_dict(configuration)
        container.init_resources()
        container.wire(modules=[sys.modules[__name__]])

        main(**{k.lower(): v for k, v in vars(namespace).items()})
    else:
        parser.print_usage()
        sys.exit(ExitCode.USAGE)

