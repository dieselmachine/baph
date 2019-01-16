import sys
from threading import Lock
from time import time

from django.core.handlers import base, wsgi
from django.http import Http404, HttpResponseNotFound
from django.utils.encoding import force_str

from baph.exceptions.http import HttpException
from .base_new import BaseHandler


class WSGIHandler(BaseHandler):
    initLock = Lock()
    request_class = wsgi.WSGIRequest

    def wsgi_app(self, environ, start_response):
        #print 'wsgi handler'
        start = time()
        ctx = self.request_context(environ)
        error = None
        try:
            try:
                ctx.push()
                response = self.full_dispatch_request()
            except Exception as e:
                print 'ERROR:', e
                raise
                error = e
                response = self.handle_exception(e)
            except BaseException as e:
                error = e
                raise

            status = '%s %s' % (response.status_code, response.reason_phrase)
            response_headers = [(str(k), str(v)) for k, v in response.items()]
            for c in response.cookies.values():
                response_headers.append((str('Set-Cookie'), str(c.output(header=''))))
            elapsed = time() - start
            #print 'WSGI call took:', elapsed
            start_response(force_str(status), response_headers)
            return response
        finally:
            if self.should_ignore_error(error):
                error = None
            ctx.auto_pop(error)

    def __call__(self, environ, start_response):
        #print '\nWSGIHandler.__call__:'
        # django
        if self._request_middleware is None:
            with self.initLock:
                try:
                    # Check that middleware is still uninitialised.
                    if self._request_middleware is None:
                        self.load_middleware()
                except:
                    # Unload whatever middleware we got
                    self._request_middleware = None
                    raise

        wsgi.set_script_prefix(base.get_script_name(environ))

        # flask
        return self.wsgi_app(environ, start_response)
