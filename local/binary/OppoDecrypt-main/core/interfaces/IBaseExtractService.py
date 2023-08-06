import abc

from .IService import IService

__author__ = 'MiuiPro.info DEV Team'
__copyright__ = 'Copyright (c) 2023 MiuiPro.info'


class IBaseExtractService(IService):
    @abc.abstractmethod
    def extract(self, **kwargs) -> None:
        """Extract"""
