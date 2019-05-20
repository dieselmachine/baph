from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponseNotFound
from django.test.client import Client as DjangoClient

from baph.core.handlers.base_new import BaseHandler
#from baph.exceptions.http import HttpException
from werkzeug.exceptions import HTTPException
from baph.globals import _request_ctx_stack


class ClientHandler(BaseHandler):
    request_class = WSGIRequest

    def __init__(self, enforce_csrf_checks=True, *args, **kwargs):
        self.enforce_csrf_checks = enforce_csrf_checks
        super(ClientHandler, self).__init__(*args, **kwargs)

    def preprocess_request(self):
        request = _request_ctx_stack.top.request
        request._dont_enforce_csrf_checks = not self.enforce_csrf_checks
        return super(ClientHandler, self).preprocess_request()

    def wsgi_app(self, environ):
        ctx = self.request_context(environ)
        error = None
        try:
            try:
                ctx.push()
                response = self.full_dispatch_request()
            except Exception as e:
                raise
                error = e
                response = self.handle_exception(e)
            except BaseException as e:
                error = e
                raise
            response.close()
            return response
        finally:
            if self.should_ignore_error(error):
                error = None
            ctx.auto_pop(error)

    def __call__(self, environ):
        if self._request_middleware is None:
            self.load_middleware()

        return self.wsgi_app(environ)


class Client(DjangoClient):
    def __init__(self, enforce_csrf_checks=False, **defaults):
        super(DjangoClient, self).__init__(**defaults)
        self.handler = ClientHandler(enforce_csrf_checks)
        self.exc_info = None

    def store_exc_info(self, **kwargs):
        """
        this needs to be a noop, otherwise django will reraise exceptions
        that were already handled
        """
        pass
