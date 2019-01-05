import sys
from importlib import import_module

from baph.apps import apps
from django.utils.module_loading import module_has_submodule
from werkzeug.local import Local, LocalProxy

from .globals import _request_ctx_stack, _app_ctx_stack
from ._compat import BROKEN_PYPY_CTXMGR_EXIT


local = Local()
_sentinel = object()


class _LocalProxy(LocalProxy):
    pass


def context_global(func):
    name = func.__name__
    def inner():
        if not hasattr(local, name):
            setattr(local, name, func())
        return getattr(local, name)
    return _LocalProxy(inner)


def collect_globals():
    """
    checks each app in INSTALLED_APPS for a globals.py file, collects all
    @context_globals in those files, and returns a dict of globals
    """
    _globals = {}
    for app in apps.get_app_configs():
        if module_has_submodule(app.module, 'globals'):
            module_name = '%s.%s' % (app.name, 'globals')
            module = import_module(module_name)
            for k, v in module.__dict__.items():
                if isinstance(v, _LocalProxy):
                    _globals[k] = v
    return _globals


def set_global(name, value):
    setattr(local, name, value)


def set_globals(**kwargs):
    for k, v in kwargs.iteritems():
        set_global(k, v)


def clear_global(name):
    """
    clears the cached value of a global variable
    """
    if hasattr(local, name):
        delattr(local, name)


def clear_globals(*names):
    """
    clears the cached values of multiple global variables
    """
    map(clear_global, names)


class _AppCtxGlobals(object):
    def __init__(self):
        from coffin.common import env
        g = collect_globals()
        self.__dict__.update(g)
        env.globals.update(g)

    def get(self, name, default=None):
        return self.__dict__.get(name, default)

    def pop(self, name, default=_sentinel):
        if default is _sentinel:
            return self.__dict__.pop(name)
        else:
            return self.__dict__.pop(name, default)

    def setdefault(self, name, default=None):
        return self.__dict__.setdefault(name, default)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __repr__(self):
        top = _app_ctx_stack.top
        if top is not None:
            return '<globals of %r>' % top.app.name
        return object.__repr__(self)


class AppContext(object):
    def __init__(self, app):
        self.app = app
        self.g = app.app_ctx_globals_class()

        # Like request context, app contexts can be pushed multiple times
        # but there a basic "refcount" is enough to track them.
        self._refcnt = 0

    def push(self):
        """Binds the app context to the current context."""
        self._refcnt += 1
        if hasattr(sys, 'exc_clear'):
            sys.exc_clear()
        _app_ctx_stack.push(self)

    def pop(self, exc=_sentinel):
        """Pops the app context."""
        try:
            self._refcnt -= 1
            if self._refcnt <= 0:
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.app.do_teardown_appcontext(exc)
        finally:
            rv = _app_ctx_stack.pop()
        assert rv is self, 'Popped wrong app context.  (%r instead of %r)' \
            % (rv, self)
        #appcontext_popped.send(self.app)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop(exc_value)

        if BROKEN_PYPY_CTXMGR_EXIT and exc_type is not None:
            reraise(exc_type, exc_value, tb)


class RequestContext(object):

    def __init__(self, app, environ, request=None):
        self.app = app
        if request is None:
            request = app.request_class(environ)
        self.request = request
        #self.url_adapter = app.create_url_adapter(self.request)
        #self.flashes = None
        #self.session = None

        self._implicit_app_ctx_stack = []
        self.preserved = False
        self._preserved_exc = None
        self._after_request_functions = []
        #self.match_request()

    def _get_g(self):
        return _app_ctx_stack.top.g
    def _set_g(self, value):
        _app_ctx_stack.top.g = value
    g = property(_get_g, _set_g)
    del _get_g, _set_g

    def copy(self):
        return self.__class__(self.app,
            environ=self.request.environ,
            request=self.request
        )

    '''
    def match_request(self):
        try:
            url_rule, self.request.view_args = \
                self.url_adapter.match(return_rule=True)
            self.request.url_rule = url_rule
        except HTTPException as e:
            self.request.routing_exception = e
    '''

    def push(self):
        #print 'push req ctx', id(self)
        top = _request_ctx_stack.top
        if top is not None and top.preserved:
            top.pop(top._preserved_exc)

        app_ctx = _app_ctx_stack.top
        #print '  app ctx:', id(app_ctx)
        #print '  app:', app_ctx.app
        if app_ctx is None or app_ctx.app != self.app:
            app_ctx = self.app.app_context()
            #print '  new app ctx', id(app_ctx)
            #print '  new app:', app_ctx.app
            app_ctx.push()
            self._implicit_app_ctx_stack.append(app_ctx)
        else:
            self._implicit_app_ctx_stack.append(None)

        if hasattr(sys, 'exc_clear'):
            sys.exc_clear()
        
        _request_ctx_stack.push(self)

        '''
        if self.session is None:
            session_interface = self.app.session_interface
            self.session = session_interface.open_session(
                self.app, self.request
            )

            if self.session is None:
                self.session = session_interface.make_null_session(self.app)
        '''

    def pop(self, exc=_sentinel):
        """Pops the request context and unbinds it by doing that.  This will
        also trigger the execution of functions registered by the
        :meth:`~flask.Flask.teardown_request` decorator.
        .. versionchanged:: 0.9
           Added the `exc` argument.
        """
        #print 'pop req ctx', id(self)
        app_ctx = self._implicit_app_ctx_stack.pop()

        try:
            clear_request = False
            if not self._implicit_app_ctx_stack:
                self.preserved = False
                self._preserved_exc = None
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.app.do_teardown_request(exc)

                # If this interpreter supports clearing the exception information
                # we do that now.  This will only go into effect on Python 2.x,
                # on 3.x it disappears automatically at the end of the exception
                # stack.
                if hasattr(sys, 'exc_clear'):
                    sys.exc_clear()

                request_close = getattr(self.request, 'close', None)
                #print 'request close:', request_close
                if request_close is not None:
                    request_close()
                clear_request = True
        finally:
            rv = _request_ctx_stack.pop()

            # get rid of circular dependencies at the end of the request
            # so that we don't require the GC to be active.
            if clear_request:
                rv.request.environ['werkzeug.request'] = None

            # Get rid of the app as well if necessary.
            if app_ctx is not None:
                app_ctx.pop(exc)
            assert rv is self, 'Popped wrong request context.  ' \
                '(%r instead of %r)' % (rv, self)

    def auto_pop(self, exc):
        #print 'autopop:', id(self)
        if self.request.environ.get('flask._preserve_context') or \
           (exc is not None and self.app.preserve_context_on_exception):
            self.preserved = True
            self._preserved_exc = exc
        else:
            self.pop(exc)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        # do not pop the request stack if we are in debug mode and an
        # exception happened.  This will allow the debugger to still
        # access the request object in the interactive shell.  Furthermore
        # the context can be force kept alive for the test client.
        # See flask.testing for how this works.
        self.auto_pop(exc_value)

        if BROKEN_PYPY_CTXMGR_EXIT and exc_type is not None:
            reraise(exc_type, exc_value, tb)

    def __repr__(self):
        return '<%s \'%s\' [%s] of %s>' % (
            self.__class__.__name__,
            self.request.url,
            self.request.method,
            self.app.name,
        )
