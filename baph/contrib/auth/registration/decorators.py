from urllib import urlencode

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.decorators import available_attrs
from django.utils.functional import wraps
from django.utils.encoding import force_str

from baph.contrib.auth.registration import settings as auth_settings


def secure_required(view_func):
    """
    Decorator to switch an url from http to https.

    If a view is accessed through http and this decorator is applied to that
    view, than it will return a permanent redirect to the secure (https)
    version of the same view.

    The decorator also must check that ``BAPH_USE_HTTPS`` is enabled. If
    disabled, it should not redirect to https because the project doesn't
    support it.

    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.is_secure():
            if auth_settings.BAPH_USE_HTTPS:
                current_host = request.META['HTTP_HOST']
                secure_host = getattr(settings, 'BAPH_SECURE_HOST', None)
                if secure_host:
                    path = request.get_full_path()
                    secure_url = 'https://%s%s' % (secure_host, path)
                    request.session['cs_host'] = current_host
                    request.session.modified = True
                else:
                    request_url = request.build_absolute_uri(request.get_full_path())
                    secure_url = request_url.replace('http://', 'https://')
                rsp = HttpResponseRedirect(secure_url)
                rsp.set_cookie('cs_host', current_host, max_age=60,
                                domain=settings.SESSION_COOKIE_DOMAIN)
                return rsp
        return view_func(request, *args, **kwargs)
    return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
