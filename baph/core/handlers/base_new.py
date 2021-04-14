import sys

from django.conf import settings
from django.core.handlers import base
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException
from werkzeug.routing import RoutingException
from werkzeug.wrappers import BaseResponse, Response

from baph.context import AppContext, RequestContext, _AppCtxGlobals
from baph.exceptions.http import HttpException, HttpImmediateResponse, HttpRedirect
from baph.globals import _request_ctx_stack, request
from ._compat import integer_types, reraise, text_type

# a singleton sentinel value for parameter defaults
_sentinel = object()


class BaseHandler(base.BaseHandler):
    middleware_setting_key = 'MIDDLEWARE_CLASSES'
    urlconf_setting_key = 'ROOT_URLCONF'
    name = 'baph'
    app_ctx_globals_class = _AppCtxGlobals
    response_class = Response

    def __init__(self, *args, **kwargs):
        #print '%s.__init__:' % type(self).__name__
        super(BaseHandler, self).__init__(*args, **kwargs)
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

    def app_context(self):
        return AppContext(self)

    def request_context(self, environ=None, request=None):
        return RequestContext(self, environ, request)

    def should_ignore_error(self, error):
        return False

    def get_urlconf(self):
        urlconf = self.urlconf_setting_key
        if isinstance(urlconf, basestring):
            urlconf = getattr(settings, urlconf)
        return urlconf

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
        from django.test.utils import override_settings
        urlconf = self.get_urlconf()
        with override_settings(ROOT_URLCONF=urlconf):
            return super(BaseHandler, self).get_response(request)

    def full_dispatch_request(self):
        #self.try_trigger_before_first_request_functions()
        try:
            #wsgi.signals.request_started.send(sender=self.__class__)
            rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request()
                print 'dispatch request returned %s' % type(rv)
        except Exception as e:
            rv = self.handle_user_exception(e)
            print 'handle user exception returned %s' % type(rv)
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

    def _make_response(self, rv):
        """Convert the return value from a view function to an instance of
        :attr:`response_class`.
        :param rv: the return value from the view function. The view function
            must return a response. Returning ``None``, or the view ending
            without returning, is not allowed. The following types are allowed
            for ``view_rv``:
            ``str`` (``unicode`` in Python 2)
                A response object is created with the string encoded to UTF-8
                as the body.
            ``bytes`` (``str`` in Python 2)
                A response object is created with the bytes as the body.
            ``dict``
                A dictionary that will be jsonify'd before being returned.
            ``tuple``
                Either ``(body, status, headers)``, ``(body, status)``, or
                ``(body, headers)``, where ``body`` is any of the other types
                allowed here, ``status`` is a string or an integer, and
                ``headers`` is a dictionary or a list of ``(key, value)``
                tuples. If ``body`` is a :attr:`response_class` instance,
                ``status`` overwrites the exiting value and ``headers`` are
                extended.
            :attr:`response_class`
                The object is returned unchanged.
            other :class:`~werkzeug.wrappers.Response` class
                The object is coerced to :attr:`response_class`.
            :func:`callable`
                The function is called as a WSGI application. The result is
                used to create a response object.
        .. versionchanged:: 0.9
           Previously a tuple was interpreted as the arguments for the
           response object.
        """

        status = headers = None

        # unpack tuple returns
        if isinstance(rv, tuple):
            len_rv = len(rv)

            # a 3-tuple is unpacked directly
            if len_rv == 3:
                rv, status, headers = rv
            # decide if a 2-tuple has status or headers
            elif len_rv == 2:
                if isinstance(rv[1], (Headers, dict, tuple, list)):
                    rv, headers = rv
                else:
                    rv, status = rv
            # other sized tuples are not allowed
            else:
                raise TypeError(
                    "The view function did not return a valid response tuple."
                    " The tuple must have the form (body, status, headers),"
                    " (body, status), or (body, headers)."
                )

        # the body must not be None
        if rv is None:
            raise TypeError(
                "The view function did not return a valid response. The"
                " function either returned None or ended without a return"
                " statement."
            )

        # make sure the body is an instance of the response class
        if not isinstance(rv, self.response_class):
            if isinstance(rv, (text_type, bytes, bytearray)):
                # let the response class set the status and headers instead of
                # waiting to do it manually, so that the class can handle any
                # special logic
                rv = self.response_class(rv, status=status, headers=headers)
                status = headers = None
            elif isinstance(rv, BaseResponse) or callable(rv):
                # evaluate a WSGI callable, or coerce a different response
                # class to the correct type
                try:
                    rv = self.response_class.force_type(rv, request.environ)
                except TypeError as e:
                    new_error = TypeError(
                        "{e}\nThe view function did not return a valid"
                        " response. The return type must be a string, dict, tuple,"
                        " Response instance, or WSGI callable, but it was a"
                        " {rv.__class__.__name__}.".format(e=e, rv=rv)
                    )
                    reraise(TypeError, new_error, sys.exc_info()[2])
            else:
                raise TypeError(
                    "The view function did not return a valid"
                    " response. The return type must be a string, dict, tuple,"
                    " Response instance, or WSGI callable, but it was a"
                    " {rv.__class__.__name__}.".format(rv=rv)
                )

        # prefer the status if it was provided
        if status is not None:
            if isinstance(status, (text_type, bytes, bytearray)):
                rv.status = status
            else:
                rv.status_code = status

        # extend existing headers with provided headers
        if headers:
            rv.headers.extend(headers)

        return rv

    def make_response(self, response):
        return response

    def process_response(self, response):
        funcs = self.after_request_funcs.get(None, ())
        for func in funcs:
            response = func(response)
        return response

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
        #local_manager.cleanup()
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

    def handle_http_exception(self, e):
        """Handles an HTTP exception.  By default this will invoke the
        registered error handlers and fall back to returning the
        exception as response.
        .. versionchanged:: 1.0.3
            ``RoutingException``, used internally for actions such as
             slash redirects during routing, is not passed to error
             handlers.
        .. versionchanged:: 1.0
            Exceptions are looked up by code *and* by MRO, so
            ``HTTPExcpetion`` subclasses can be handled with a catch-all
            handler for the base ``HTTPException``.
        .. versionadded:: 0.3
        """
        # Proxy exceptions don't have error codes.  We want to always return
        # those unchanged as errors
        print '\nhandle_http_exception:', (e, e.code)
        if e.code is None:
            return e

        # RoutingExceptions are used internally to trigger routing
        # actions, such as slash redirects raising RequestRedirect. They
        # are not raised or handled in user code.
        if isinstance(e, RoutingException):
            return e
        if isinstance(e, HttpRedirect):
            print 'is redirect'
            return e.get_response()

        handler = self._find_error_handler(e)
        if handler is None:
            return e
        return handler(e)

    def trap_http_exception(self, e):
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
        print '\nhandle_user_exception: %r' % e
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

        if isinstance(e, HttpImmediateResponse):
            return e.response
        #if isinstance(e, HTTPException) and not self.trap_http_exception(e):
        #    return self.handle_http_exception(e)
        if isinstance(e, HttpException) and not self.trap_http_exception(e):
            return self.handle_http_exception(e)

        handler = self._find_error_handler(e)
        if handler is None:
            reraise(exc_type, exc_value, tb)
        return handler(e)

    @staticmethod
    def _get_exc_class_and_code(exc_class_or_code):
        """Ensure that we register only exceptions as handler keys"""
        #print 'get exc class and code:', exc_class_or_code
        if isinstance(exc_class_or_code, integer_types):
            exc_class = default_exceptions[exc_class_or_code]
        else:
            exc_class = exc_class_or_code

        assert issubclass(exc_class, Exception)

        if issubclass(exc_class, HttpException):
            return exc_class, exc_class.code
        elif issubclass(exc_class, HTTPException):
            return exc_class, exc_class.code
        else:
            return exc_class, None

    def _find_error_handler(self, e):
        """Return a registered error handler for an exception in this order:
        blueprint handler for a specific code, app handler for a specific code,
        blueprint handler for an exception class, app handler for an exception
        class, or ``None`` if a suitable handler is not found.
        """
        print 'find error handler:', self, e
        exc_class, code = self._get_exc_class_and_code(type(e))
        print exc_class, code
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
