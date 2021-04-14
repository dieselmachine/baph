import time

from django.core.urlresolvers import get_resolver, set_urlconf, RegexURLPattern, Resolver404

from baph.utils.module_loading import import_string

from .base import BaseHandler


PROXY_VIEW_NAME = '__PROXY'


def proxy_view(request, *args, **kwargs):
    from django.conf import settings
    callback_name = settings.PROXY_DEFAULT_VIEW
    callback = import_string(callback_name)
    return callback(request, *args, **kwargs)


def get_proxy_resolver(urlconf, default_view=None):
    set_urlconf(urlconf)

    resolver = get_resolver(urlconf)
    module = resolver.urlconf_module
    names = set([p.name for p in module.urlpatterns])

    if PROXY_VIEW_NAME in names:
        # proxy handler view already installed
        return resolver

    # before installing the catchall handler, ensure no other catchall
    # exists, as it will prevent the proxy view from being hit
    try:
        resolver.resolve('/__%x/' % int(time.time()))
        raise Exception('proxy default view cannot be installed because '
                        'of an existing catchall pattern')
    except Resolver404:
        pass

    callback = proxy_view
    pattern = RegexURLPattern(r'', callback, name=PROXY_VIEW_NAME)
    resolver.url_patterns.append(pattern)
    return resolver


class ProxyHandler(BaseHandler):
    middleware_setting_key = 'PROXY_MIDDLEWARE'
    urlconf_setting_key = 'PROXY_URLCONF'

    def __init__(self, *args, **kwargs):
        super(ProxyHandler, self).__init__(*args, **kwargs)
        self.load_middleware()

    def get_resolver(self, urlconf=None):
        """
        Loads the urlresolver with the given urlconf, then appends the default
        proxy view as a catchall at the end of the pattern list
        """
        if urlconf is None:
            from django.conf import settings
            urlconf = getattr(settings, self.urlconf_setting_key)
        return get_proxy_resolver(urlconf)


proxy_handler = ProxyHandler()
