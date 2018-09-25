from __future__ import unicode_literals

from functools import update_wrapper
import logging
import sys
import types
import warnings

from django.conf import settings
from django.core import signals
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
from django.core.handlers import base
from django.core.urlresolvers import get_urlconf, set_urlconf, RegexURLResolver
from django.db import connections, transaction
#from django.test.utils import override_settings
from django.utils import six
from werkzeug.local import LocalManager
from werkzeug.exceptions import HTTPException

from baph.conf import local as settings_local
from baph.context import AppContext, RequestContext, _AppCtxGlobals, local
from baph.exceptions.http import HttpException
from baph.globals import _request_ctx_stack, g, request, session
from baph.utils.module_loading import import_string

from ._compat import integer_types, reraise
from .exception import (
    convert_exception_to_response, get_exception_response,
    handle_uncaught_exception,
)
from utils import get_resolver

logger = logging.getLogger('django.request')

# a singleton sentinel value for parameter defaults
_sentinel = object()

local_manager = LocalManager([settings_local, local])

def setupmethod(f):
    """Wraps a method so that it performs a check in debug mode if the
    first request was already handled.
    """
    def wrapper_func(self, *args, **kwargs):
        if self.debug and self._got_first_request:
            raise AssertionError('A setup function was called after the '
                'first request was handled.  This usually indicates a bug '
                'in the application where a module was not imported '
                'and decorators or other functionality was called too late.\n'
                'To fix this make sure to import all your view modules, '
                'database models and everything related at a central place '
                'before the application starts serving requests.')
        return f(self, *args, **kwargs)
    return update_wrapper(wrapper_func, f)


class BaseHandler(base.BaseHandler):
    middleware_setting_key = 'MIDDLEWARE_CLASSES'
    urlconf_setting_key = 'ROOT_URLCONF'
    name = 'baph'
    app_ctx_globals_class = _AppCtxGlobals

    def __init__(self, *args, **kwargs):
        #print '%s.__init__:' % type(self).__name__
        super(BaseHandler, self).__init__(*args, **kwargs)
        self.derp = True
        self.error_handler_spec = {}
        self.after_request_funcs = {}
        self.before_request_funcs = {}
        self.teardown_request_funcs = {}
        self.teardown_appcontext_funcs = []
        self.debug = getattr(settings, 'DEBUG', False)
        self.testing = getattr(settings, 'IS_TEST', False)

    @property
    def preserve_context_on_exception(self):
        """Returns the value of the ``PRESERVE_CONTEXT_ON_EXCEPTION``
        configuration value in case it's set, otherwise a sensible default
        is returned.
        .. versionadded:: 0.7
        """
        #rv = self.config['PRESERVE_CONTEXT_ON_EXCEPTION']
        rv = getattr(settings, 'PRESERVE_CONTEXT_ON_EXCEPTION', None)
        if rv is not None:
            return rv
        return self.debug

    @property
    def propagate_exceptions(self):
        """Returns the value of the ``PROPAGATE_EXCEPTIONS`` configuration
        value in case it's set, otherwise a sensible default is returned.
        .. versionadded:: 0.7
        """
        #rv = self.config['PROPAGATE_EXCEPTIONS']
        rv = getattr(settings, 'DEBUG_PROPAGATE_EXCEPTIONS', None)
        if rv is not None:
            return rv
        return self.testing or self.debug

    def get_urlconf(self):
        urlconf = self.urlconf_setting_key
        if isinstance(urlconf, basestring):
            urlconf = getattr(settings, urlconf)
        return urlconf

    def __setattr__(self, key, value):
        super(BaseHandler, self).__setattr__(key, value)

    @staticmethod
    def _get_exc_class_and_code(exc_class_or_code):
        """Ensure that we register only exceptions as handler keys"""
        #print 'get exc class and code:', exc_class_or_code
        if isinstance(exc_class_or_code, integer_types):
            exc_class = default_exceptions[exc_class_or_code]
        else:
            exc_class = exc_class_or_code

        assert issubclass(exc_class, Exception)

        if issubclass(exc_class, HTTPException):
            return exc_class, exc_class.code
        else:
            return exc_class, None

    def _find_error_handler(self, e):
        """Return a registered error handler for an exception in this order:
        blueprint handler for a specific code, app handler for a specific code,
        blueprint handler for an exception class, app handler for an exception
        class, or ``None`` if a suitable handler is not found.
        """
        #print 'find error handler:', self, e
        exc_class, code = self._get_exc_class_and_code(type(e))
        '''
        for name, c in (
            (request.blueprint, code), (None, code),
            (request.blueprint, None), (None, None)
        ):
        '''
        for name, c in (
            (None, code), (None, None)
        ):
            handler_map = self.error_handler_spec.setdefault(name, {}).get(c)

            if not handler_map:
                continue

            for cls in exc_class.__mro__:
                handler = handler_map.get(cls)

                if handler is not None:
                    return handler

    def load_middleware(self):
        """
        Populate middleware lists from settings

        Must be called after the environment is fixed (see __call__ in subclasses).
        """
        #print '%s.load middleware:' % type(self).__name__
        from django.test.utils import override_settings
        middleware = getattr(settings, self.middleware_setting_key, ())
        with override_settings(MIDDLEWARE_CLASSES=middleware):
            super(BaseHandler, self).load_middleware()

    def get_response(self, request):
        #urlconf = getattr(settings, self.urlconf_setting_key)
        from django.test.utils import override_settings
        urlconf = self.get_urlconf()
        with override_settings(ROOT_URLCONF=urlconf):
            return super(BaseHandler, self).get_response(request)

    def app_context(self):
        return AppContext(self)

    def request_context(self, environ):
        return RequestContext(self, environ)

    def should_ignore_error(self, error):
        return False

    @setupmethod
    def before_request(self, f):
        """Registers a function to run before each request.
        For example, this can be used to open a database connection, or to load
        the logged in user from the session.
        The function will be called without any arguments. If it returns a
        non-None value, the value is handled as if it was the return value from
        the view, and further request handling is stopped.
        """
        self.before_request_funcs.setdefault(None, []).append(f)
        return f

    @setupmethod
    def teardown_request(self, f):
        """Register a function to be run at the end of each request,
        regardless of whether there was an exception or not.  These functions
        are executed when the request context is popped, even if not an
        actual request was performed.
        Example::
            ctx = app.test_request_context()
            ctx.push()
            ...
            ctx.pop()
        When ``ctx.pop()`` is executed in the above example, the teardown
        functions are called just before the request context moves from the
        stack of active contexts.  This becomes relevant if you are using
        such constructs in tests.
        Generally teardown functions must take every necessary step to avoid
        that they will fail.  If they do execute code that might fail they
        will have to surround the execution of these code by try/except
        statements and log occurring errors.
        When a teardown function was called because of an exception it will
        be passed an error object.
        The return values of teardown functions are ignored.
        .. admonition:: Debug Note
           In debug mode Flask will not tear down a request on an exception
           immediately.  Instead it will keep it alive so that the interactive
           debugger can still access it.  This behavior can be controlled
           by the ``PRESERVE_CONTEXT_ON_EXCEPTION`` configuration variable.
        """
        self.teardown_request_funcs.setdefault(None, []).append(f)
        return f

    def do_teardown_appcontext(self, exc=_sentinel):
        """Called right before the application context is popped.
        When handling a request, the application context is popped
        after the request context. See :meth:`do_teardown_request`.
        This calls all functions decorated with
        :meth:`teardown_appcontext`. Then the
        :data:`appcontext_tearing_down` signal is sent.
        This is called by
        :meth:`AppContext.pop() <flask.ctx.AppContext.pop>`.
        .. versionadded:: 0.9
        """
        if exc is _sentinel:
            exc = sys.exc_info()[1]
        for func in reversed(self.teardown_appcontext_funcs):
            func(exc)
        local_manager.cleanup()
        #appcontext_tearing_down.send(self, exc=exc)

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

    def full_dispatch_request(self):
        #self.try_trigger_before_first_request_functions()
        try:
            #wsgi.signals.request_started.send(sender=self.__class__)
            rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request()
        except Exception as e:
            rv = self.handle_user_exception(e)
        return self.finalize_request(rv)

    def preprocess_request(self):
        funcs = self.before_request_funcs.get(None, ())
        for func in funcs:
            rv = func()
            if rv is not None:
                return rv

    def dispatch_request(self):
        req = _request_ctx_stack.top.request
        response = self.get_response(req)
        response._handler_class = self.__class__
        return response

    def finalize_request(self, rv, from_error_handler=False):
        response = self.make_response(rv)
        try:
            response = self.process_response(response)
            #request_finished.send(self, response=response)
        except Exception:
            if not from_error_handler:
                raise
            self.logger.exception('Request finalizing failed with an '
                                  'error while handling an error')
        return response

    def make_response(self, response):
        return response

    def process_response(self, response):
        funcs = self.after_request_funcs.get(None, ())
        for func in funcs:
            response = func(response)
        return response

    def handle_exception(self, e):
        """Default exception handling that kicks in when an exception
        occurs that is not caught.  In debug mode the exception will
        be re-raised immediately, otherwise it is logged and the handler
        for a 500 internal server error is used.  If no such handler
        exists, a default 500 internal server error message is displayed.
        .. versionadded:: 0.3
        """
        exc_type, exc_value, tb = sys.exc_info()

        #got_request_exception.send(self, exception=e)
        handler = self._find_error_handler(InternalServerError())

        if self.propagate_exceptions:
            # if we want to repropagate the exception, we can attempt to
            # raise it with the whole traceback in case we can do that
            # (the function was actually called from the except part)
            # otherwise, we just raise the error again
            if exc_value is e:
                reraise(exc_type, exc_value, tb)
            else:
                raise e

        #self.log_exception((exc_type, exc_value, tb))
        if handler is None:
            return InternalServerError()
        return self.finalize_request(handler(e), from_error_handler=True)

    def handle_http_exception(self, e):
        """Handles an HTTP exception.  By default this will invoke the
        registered error handlers and fall back to returning the
        exception as response.
        .. versionadded:: 0.3
        """
        # Proxy exceptions don't have error codes.  We want to always return
        # those unchanged as errors
        if e.code is None:
            return e
        return e.get_response()
        '''
        handler = self._find_error_handler(e)
        if handler is None:
            return e
        return handler(e)
        '''

    def trap_http_exception(self, e):
        if getattr(settings, 'TRAP_HTTP_EXCEPTIONS', False):
            return True

        trap_bad_request = getattr(settings, 'TRAP_BAD_REQUEST_ERRORS', None)
        '''
        if (
            trap_bad_request is None and self.debug
            and isinstance(e, BadRequestKeyError)
        ):
            return True

        if trap_bad_request:
            return isinstance(e, BadRequest)
        '''
        return False

    def handle_user_exception(self, e):
        """This method is called whenever an exception occurs that should be
        handled.  A special case are
        :class:`~werkzeug.exception.HTTPException`\s which are forwarded by
        this function to the :meth:`handle_http_exception` method.  This
        function will either return a response value or reraise the
        exception with the same traceback.
        .. versionchanged:: 1.0
            Key errors raised from request data like ``form`` show the the bad
            key in debug mode rather than a generic bad request message.
        .. versionadded:: 0.7
        """
        exc_type, exc_value, tb = sys.exc_info()
        assert exc_value is e
        # ensure not to trash sys.exc_info() at that point in case someone
        # wants the traceback preserved in handle_http_exception.  Of course
        # we cannot prevent users from trashing it themselves in a custom
        # trap_http_exception method so that's their fault then.

        # MultiDict passes the key to the exception, but that's ignored
        # when generating the response message. Set an informative
        # description for key errors in debug mode or when trapping errors.
        '''
        if (
            #(self.debug or self.config['TRAP_BAD_REQUEST_ERRORS'])
            (self.debug or getattr(settings, 'TRAP_BAD_REQUEST_ERRORS', False))
            and isinstance(e, BadRequestKeyError)
            # only set it if it's still the default description
            and e.description is BadRequestKeyError.description
        ):
            e.description = "KeyError: '{0}'".format(*e.args)
        '''

        #if isinstance(e, HTTPException) and not self.trap_http_exception(e):
        #    return self.handle_http_exception(e)
        if isinstance(e, HttpException) and not self.trap_http_exception(e):
            return self.handle_http_exception(e)

        handler = self._find_error_handler(e)

        if handler is None:
            reraise(exc_type, exc_value, tb)
        return handler(e)