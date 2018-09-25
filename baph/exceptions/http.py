from abc import ABCMeta, abstractmethod


class HttpException(Exception):
    """Base http exception"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_response(self):
        pass

    @property
    def code(self):
        return self.status