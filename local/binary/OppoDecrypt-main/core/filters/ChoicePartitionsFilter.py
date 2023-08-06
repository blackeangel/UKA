__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class ChoicePartitionsFilter:
    def __call__(self, choices, *args, **kwargs):
        result = []
        for item in choices:
            if isinstance(item, list):
                result.extend(item)
                continue

            if item.name not in [_.name for _ in result]:
                result.append(item)

        return result
