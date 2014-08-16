from baph.contrib import auth
from baph.contrib.auth import load_backend
from baph.contrib.auth.models import Organization
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject


def get_org(request):
    if not hasattr(request, '_cached_org'):
        request._cached_org = Organization.get_from_request(request)
    return request._cached_org

def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = auth.get_user(request)
    return request._cached_user

class OrganizationMiddleware(object):
    def process_request(self, request):
        if hasattr(request, 'user'):
            raise ImproperlyConfigured("OrganizationMiddleware must be "
                "loaded before AuthenticationMiddleware")
        request.org = SimpleLazyObject(lambda: get_org(request))

class AuthenticationMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE_CLASSES setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        request.user = SimpleLazyObject(lambda: get_user(request))
        
"""
class LazyUser(object):
    '''Allows for the lazy retrieval of the :class:`baph.auth.models.User`
    object.
    '''
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user'):
            from . import get_user
            request._cached_user = get_user(request)
        return request._cached_user


class AuthenticationMiddleware(object):
    '''See :class:`django.contrib.auth.middleware.AuthenticationMiddleware`.
    '''

    def process_request(self, request):
        assert hasattr(request, 'session'), '''\
The Django authentication middleware requires session middleware to be
installed. Edit your MIDDLEWARE_CLASSES setting to insert
"django.contrib.sessions.middleware.SessionMiddleware".'''
        request.__class__.user = LazyUser()
        return None
"""
