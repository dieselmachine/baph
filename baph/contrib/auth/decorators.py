from functools import wraps
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.utils.decorators import available_attrs
from django.utils.encoding import force_str
from django.utils.six.moves.urllib.parse import urlparse
from django.shortcuts import resolve_url

import decorator as _decorator
import logging
import time

#from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect


def user_passes_test(test_func, login_url=None, 
                      redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            # urlparse chokes on lazy objects in Python 3, force to str
            resolved_login_url = force_str(
                resolve_url(login_url or settings.LOGIN_URL))
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(
                path, resolved_login_url, redirect_field_name)
        return _wrapped_view
    return decorator

def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, 
                   login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def check_perm(resource, action, simple=True, extra_keys={}, filters={}):
    ''' checks user permissions to determine whether to allow user access
    :resource: [string] corresponds to 'resource' value in db, ex: 'site'
    :action: [string] corresponds to 'action' value in db, ex 'view'
    :simple: [bool] True = checks if any permission exists for the 
    :   resource.action pair. False = apply base filters, extra_keys,
    :   and filters to a model to determine more granular permissions
    :extra_keys: [dict] each key is a param to extract from kwargs and each
    :   value is the corresponding db field, ex {'site_hash','hash'}
    :filters: [dict] key/value pairs of filter conditions to apply to
    :   the model query, ex {'deleted':0}
    '''
    def check_perm_closure(f, request, *args, **kwargs):

        if not kwargs:
            keys = f.func_code.co_varnames[1:] #item 0 is 'request'
            kwargs = dict(zip(keys,args))
            args = []

        for url_key, db_key in extra_keys.items():
            filters[db_key] = kwargs[url_key]

        if request.user.has_perm(resource, action, filters):
            return f(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')

    return decorator.decorator(check_perm_closure)

def superuser_required(function=None,
                       redirect_field_name=REDIRECT_FIELD_NAME):
    '''Decorator for views that checks that the user is a superuser,
    redirecting to the log-in page if necessary. Derived from
    django.contrib.auth.decorators.login_required.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def staff_required(function=None,
                   redirect_field_name=REDIRECT_FIELD_NAME):
    '''Decorator for views that checks that the user is a staff member,
    redirecting to the log-in page if necessary. Derived from
    django.contrib.auth.decorators.login_required.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_staff,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        logging.debug('%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper

def permission_required(perm, login_url=None, raise_exception=False):
    def check_perm_closure(view_func, view_base, request, *args, **kwargs):
        keys = view_func.func_code.co_varnames[2:] #item 0 is 'request'
        kwargs.update(dict(zip(keys,args)))
        cid = request.user.client_id
        #assert False
        cls = view_base._meta.model
        if not request.user.has_perm(cls._meta.object_name, perm, filters=kwargs):
            raise PermissionDenied()
            assert False
        return view_func(view_base, request, *args, **kwargs)
        """
        p1 = request.user.permission_assocs
        p2 = request.user.auth.permission_assocs
        g1 = request.user.user_groups
        #assert False
        if not kwargs:
            keys = f.func_code.co_varnames[1:] #item 0 is 'request'
            kwargs = dict(zip(keys,args))
            args = []

        for url_key, db_key in extra_keys.items():
            filters[db_key] = kwargs[url_key]

        if request.user.has_perm(resource, action, filters):
            return f(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')
        """
    return _decorator.decorator(check_perm_closure)
