from django.core import urlresolvers
from django.core.urlresolvers import set_urlconf, RegexURLPattern

from baph.utils.module_loading import import_string

from .base import BaseHandler
#from .utils import get_resolver


def get_proxy_resolver(urlconf, default_view):
    print 'get proxy resolver:'
    print '  urlconf:', urlconf
    print '  default view:', default_view
    from django.conf import settings
    urlresolvers.set_urlconf(urlconf)
    resolver = urlresolvers.get_resolver(urlconf)
    if isinstance(default_view, basestring):
        callback = import_string(default_view)
    else:
        callback = default_view
    resolver.handler404 = callback
    '''
    print '  callback:', callback
    if callback not in resolver.reverse_dict:
        print '  adding default view to resolver with id %s' % id(resolver)
        pattern = RegexURLPattern(r'', callback)
        resolver.url_patterns.append(pattern)
        print resolver.reverse_dict
    '''
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
        print 'get resolver', urlconf
        from django.conf import settings
        resolver = super(ProxyHandler, self).get_resolver(urlconf)
        view = urlresolvers.get_callable(settings.PROXY_DEFAULT_VIEW)
        resolver.urlconf_module.handler404 = view
        print 'attached 404 func'
        return resolver
        
        #assert False
        if urlconf is None:
            from django.conf import settings
            urlconf = getattr(settings, self.urlconf_setting_key)
        resolver = urlresolvers.get_resolver(urlconf)
        print resolver, dir(resolver)
        print resolver.urlconf_module
        callback_name = settings.PROXY_DEFAULT_VIEW
        return get_proxy_resolver(urlconf, callback_name)


proxy_handler = ProxyHandler()
