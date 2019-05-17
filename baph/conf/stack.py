import operator

from chainmap import ChainMap
from werkzeug.local import LocalProxy

from baph.globals import current_app


_cache = LocalProxy(dict)

class SettingsStack(object):

    def __init__(self, *maps):
        #print '  %s.__init__:' % type(self).__name__
        #self.source = ChainMap(*maps)
        self._wrapped = ChainMap({}, *maps)
        self.loaders = {}
        self._cache = _cache

    def __getattr__(self, key):
        #if key == 'DEBUG':
        #    print 'stack.getattr:', key

        if key in self._cache:
            #if key == 'DEBUG':
            #    print '  in cache'
            return self._cache[key]
        elif key.startswith('get_'):
            # attempted lookup of undefined getter func
            #if key == 'DEBUG':
            #    print '  undefined getter'
            self._cache[key] = None
            raise AttributeError()
        elif hasattr(self, 'get_%s' % key):
            # reduce values using a custom getter func
            #if key == 'DEBUG':
            #    print '  defined getter'
            func = getattr(self, 'get_%s' % key)
            getter = operator.methodcaller('get', key, None)
            values = filter(bool, map(getter, self._wrapped.maps))
            value = func(values)
        elif not current_app:
            try:
                value = self._wrapped.maps[-1][key]
            except KeyError:
                #print 'OOPS', key, type(self._wrapped.maps[-1])
                #print self.configured
                raise AttributeError()
        else:
            try:
                value = self._wrapped[key]
                #if key == 'DEBUG':
                #    print '  value:', value
            except KeyError:
                raise AttributeError()

        #print 'cache[%s] = %s' % (key, value)
        #self._cache[key] = value
        return value

    def __setattr__(self, key, value):
        # we don't want any values stored on the stack object
        # so we proxy to the base settings
        #print 'stack.setattr:', (key, value)
        if not key.isupper():
            #print 'setting %s to %r on %r' % (key, value, self)
            super(SettingsStack, self).__setattr__(key, value)
        else:
            #print 'setting %s to %r on %r' % (key, value, self._wrapped)
            self._wrapped[key] = value
            #setattr(self._wrapped, key, value)

    @property
    def configured(self):
        return self._wrapped.maps[-1]['configured']

    def add_settings_loader(self, module):
        self.push_ctx(module)
        #print 'settings pushed'

    def push_ctx(self, ctx, name=None):
        #print 'push ctx:', len(self.chainmap.maps)
        #if len(self.chainmap.maps) > 1:
        #    assert False
        self._wrapped.maps.insert(1, ctx)
        if name:
            self.loaders[name] = ctx

    # common reducers

    def concat(self, values):
        return reduce(operator.concat, values, '')

    def rconcat(self, values):
        return self.concat(reversed(values))

    def extend(self, values):
        return reduce(operator.concat, values, [])

    def prepend(self, values):
        return self.extend(reversed(values))

    def merge(self, values):
        return ChainMap(*values)
