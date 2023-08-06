import dataclasses

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


@dataclasses.dataclass
class CsvRecordModel:
    id: int = dataclasses.field(init=False)
    init_value: dataclasses.InitVar[dict]
    name: str = dataclasses.field(init=False)
    images: list[str] = dataclasses.field(init=False)

    def __post_init__(self, init_value):
        self.id = int(init_value.pop('nv_id', 0), 2)
        self.name = init_value.pop('nv_text', 'Unknown')
        self.images = [item for item in init_value.values()]
