from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator

from core.models.super import MetadataPartitionModel
from core.filters import ChoicePartitionsFilter
from core.validators import SupersImgCompareCsvValidator

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class Cli:
    @staticmethod
    def get_super_map_path(input_files: list[Path]) -> Path:
        return inquirer.filepath(
            message="Enter super_map.csv file path",
            validate=SupersImgCompareCsvValidator(list_files=input_files, message="Input file is not a valid"),
            only_files=True,
            mandatory=True,
            filter=lambda result: Path(result).resolve()
        ).execute()

    @staticmethod
    def get_choice_build_configuration(choices: list[Choice]) -> list[Path]:
        return inquirer.select(
            message="Select build:",
            choices=choices,
            multiselect=False,
            transformer=lambda result: f"{result} selected",
        ).execute()

    @staticmethod
    def get_choice_extraction_partitions(choices: list[Choice]) -> list[MetadataPartitionModel]:
        return inquirer.checkbox(
            message="Select extract partitions:",
            choices=choices,
            height=len(choices),
            validate=lambda result: len(result) >= 1,
            mandatory=True,
            filter=ChoicePartitionsFilter(),
            transformer=lambda result: f"{result} selected",
        ).execute()

    @staticmethod
    def get_extract_folder(output_folder: Path):
        return inquirer.filepath(
            message="Enter extract folder",
            default=output_folder.__str__(),
            validate=PathValidator(is_file=False, is_dir=True, message="Input is not a dir"),
            only_directories=True,
            mandatory=True,
            filter=lambda result: Path(result).resolve()
        ).execute()
