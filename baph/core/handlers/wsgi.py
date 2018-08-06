import sys

from django.core.handlers import base, wsgi
from django.utils.encoding import force_str
from werkzeug.local import LocalManager

from baph.conf import local as settings_local
from baph.context import AppContext, RequestContext, _AppCtxGlobals, local
from baph.globals import _request_ctx_stack, g, request, session


# a singleton sentinel value for parameter defaults
_sentinel = object()

local_manager = LocalManager([settings_local, local])

class WSGIHandler(wsgi.WSGIHandler):
    name = 'baph'
    app_ctx_globals_class = _AppCtxGlobals

    def __init__(self, *args, **kwargs):
        super(WSGIHandler, self).__init__(*args, **kwargs)
        self.before_request_funcs = {}
        self.teardown_request_funcs = {}

    def app_context(self):
        return AppContext(self)

    def do_teardown_request(self, exc=_sentinel):
        if exc is _sentinel:
            exc = sys.exc_info()[1]
        funcs = reversed(self.teardown_request_funcs.get(None, ()))
        #bp = _request_ctx_stack.top.request.blueprint
        #if bp is not None and bp in self.teardown_request_funcs:
        #    funcs = chain(funcs, reversed(self.teardown_request_funcs[bp]))
        for func in funcs:
            func(exc)
        #request_tearing_down.send(self, exc=exc)

    def request_context(self, environ):
        return RequestContext(self, environ)

    def should_ignore_error(self, error):
        return False

    def make_response(self, rv, start_response):
        status = headers = None
        status = '%s %s' % (rv.status_code, rv.reason_phrase)
        headers = [(str(k), str(v)) for k, v in rv.items()]
        for c in rv.cookies.values():
            headers.append((str('Set-Cookie'), str(c.output(header=''))))
        start_response(force_str(status), response_headers)

    def dispatch_request(self, start_response):
        req = _request_ctx_stack.top.request
        response = self.get_response(req)
        response._handler_class = self.__class__

        status = '%s %s' % (response.status_code, response.reason_phrase)
        response_headers = [(str(k), str(v)) for k, v in response.items()]
        for c in response.cookies.values():
            response_headers.append((str('Set-Cookie'), str(c.output(header=''))))
        start_response(force_str(status), response_headers)
        return response

    def preprocess_request(self):
        '''
        bp = _request_ctx_stack.top.request.blueprint

        funcs = self.url_value_preprocessors.get(None, ())
        if bp is not None and bp in self.url_value_preprocessors:
            funcs = chain(funcs, self.url_value_preprocessors[bp])
        for func in funcs:
            func(request.endpoint, request.view_args)
        '''
        funcs = self.before_request_funcs.get(None, ())
        #if bp is not None and bp in self.before_request_funcs:
        #    funcs = chain(funcs, self.before_request_funcs[bp])
        for func in funcs:
            rv = func()
            if rv is not None:
                return rv

    def full_dispatch_request(self, start_response):
        #self.try_trigger_before_first_request_functions()
        wsgi.signals.request_started.send(sender=self.__class__)
        try:
            rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request(start_response)
        except Exception as e:
            raise
            rv = self.handle_user_exception(e)
        return rv #self.finalize_request(rv)

    def finalize_request(self, rv, from_error_handler=False):
        response = self.make_response(rv)
        try:
            response = self.process_response(response)
            request_finished.send(self, response=response)
        except Exception:
            if not from_error_handler:
                raise
            self.logger.exception('Request finalizing failed with an '
                                  'error while handling an error')
        return response

    def wsgi_app(self, environ, start_response):
        ctx = self.request_context(environ)
        error = None
        try:
            try:
                print 'try'
                ctx.push()
                response = self.full_dispatch_request(start_response)
                print 'yes'
            except Exception as e:
                print 'oops', e
                raise
                error = e
                response = self.handle_exception(e)
            except:
                print 'oops 2'
                error = sys.exc_info()[1]
                raise
            return response
        finally:
            if self.should_ignore_error(error):
                error = None
            ctx.auto_pop(error)
            local_manager.cleanup()

    def __call__(self, environ, start_response):
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