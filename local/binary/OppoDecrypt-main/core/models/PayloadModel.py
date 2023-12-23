import  dataclasses
from pathlib import Path

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


@dataclasses.dataclass
class PayloadModel:
    input_file: Path | list[Path] | None = None
    output_dir: Path | list[Path] | None = None
    search_pattern: str = "super*.img"
