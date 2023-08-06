import shutil
from functools import wraps
from pathlib import Path

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class CheckOutputFolder:
    def __new__(cls, decorated_func=None, **kwargs):
        self = super().__new__(cls)

        return self.__call__(decorated_func) if decorated_func else self

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for item in args:
                if isinstance(item, Path):
                    if item.exists():
                        shutil.rmtree(item)

                    item.mkdir(parents=True)

            return func(*args, **kwargs)
        return wrapper
