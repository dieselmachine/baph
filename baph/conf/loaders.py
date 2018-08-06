from collections import Mapping
import operator

from chainmap import ChainMap


class BaseLoader(Mapping):

    def __init__(self, source):
        print '  %s.__init__:' % type(self).__name__
        if not source:
            assert False
        self.source = source

    def getitem(self, key):
        # must be overridden in subclasses
        raise KeyError()

    def normalize_key(self, key):
        return key

    def __getitem__(self, key):
        key = self.normalize_key(key)
        return self.getitem(key)

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        for key in self.source:
            if not key.startswith('_'):
                yield self.normalize_key(key)


class AttrLoader(BaseLoader):
    def __iter__(self):
        for key in self.source.__dict__:
            if not key.startswith('_'):
                yield self.normalize_key(key)

    def getitem(self, key):
        try:
            return getattr(self.source, key)
        except AttributeError:
            raise KeyError()


class DictLoader(BaseLoader):
    def getitem(self, key):
        return self.source[key]

class ContextStack(ChainMap):

    def __getitem__(self, key):
        if hasattr(self, 'get_%s' % key):
            func = getattr(self, 'get_%s' % key)
            getter = operator.methodcaller('get', key, None)
            values = filter(bool, map(getter, self.maps))
            return func(values)
        else:
            return super(ContextStack, self).__getitem__(key)

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


class SettingsStack(object):

    def __init__(self, *maps):
        print '  %s.__init__:' % type(self).__name__
        self.chainmap = ChainMap()

    def __getattr__(self, key):
        if key.startswith('get_'):
            # attempted lookup of undefined getter func
            raise AttributeError()
        elif hasattr(self, 'get_%s' % key.lower()):
            # reduce values using a custom getter func
            func = getattr(self, 'get_%s' % key.lower())
            getter = operator.methodcaller('get', key, None)
            values = filter(bool, map(getter, self.chainmap.maps))
            return func(values)
        elif key in self.chainmap:
            # return a single value
            return self.chainmap[key]
        else:
            # no value exists
            raise AttributeError()

    def push_ctx(self, ctx):
        print 'push ctx:', len(self.chainmap.maps)
        self.chainmap.maps.append(ctx)

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

