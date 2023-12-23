from functools import wraps

from InquirerPy import inquirer

from core.models import PayloadModel

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class ConfirmationExecution:
    def __init__(self, message: str, forced: bool = False):
        self._message = message
        self._forced = forced

    def __call__(self, func):
        @wraps(func)
        def wrapper(cls, payload: PayloadModel, **kwargs):
            if payload.input_file is None or self._forced:
                proceed = inquirer.confirm(message=self._message, default=True).execute()
                if proceed:
                    return func(cls, payload, **kwargs)
                else:
                    return payload
            else:
                return func(cls, payload)
        return wrapper
