from abc import ABCMeta, abstractmethod

from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect


class HttpException(Exception):
    """Base http exception"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_response(self):
        pass


class HttpImmediateResponse(Exception):
    def __init__(self, response):
        self.response = response


class HttpRedirect(HttpException):
    def __init__(self, new_url):
        self.new_url = new_url


class Http301(HttpRedirect):
    code = 301

    def get_response(self):
        return HttpResponsePermanentRedirect(self.new_url)


class Http302(HttpRedirect):
    code = 302

    def get_response(self):
        return HttpResponseRedirect(self.new_url)


exc_map = {
    301: Http301,
    302: Http302,
}
