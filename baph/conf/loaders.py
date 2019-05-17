from collections import Mapping
import operator

from baph.globals import current_app
from chainmap import ChainMap


class BaseLoader(Mapping):
    """
    base wrapper class to wrap settings. provides dict-like interface
    to allow 'stacking' in a chainmap
    """

    def __init__(self, source, module=None, dict=None):
        self.source = source

    def __getitem__(self, key):
        key = self.normalize_key(key)
        return self.getitem(key)

    def __len__(self):
        return len(list(iter(self)))

    def __iter__(self):
        for key in self._iter():
            if not key.startswith('_'):
                yield self.normalize_key(key)

    def getitem(self, key):
        # must be overridden in subclasses
        raise KeyError()

    def normalize_key(self, key):
        return key


class AttrLoader(BaseLoader):
    """
    wrapper class for module-based settings
    """
    def _iter(self):
        #print '_iter:'
        for key in dir(self.source):
            yield key

    def getitem(self, key):
        try:
            return getattr(self.source, key)
        except AttributeError:
            raise KeyError()

    def __contains__(self, key):
        #print 'a contains', sorted(self.source.__dict__.keys())
        try:
            getattr(self.source, key)
            return True
        except AttributeError:
            return False


class DictLoader(BaseLoader):
    """
    wrapper class for dict-based settings
    """
    def _iter(self):
        for key in self.source:
            yield key

    def getitem(self, key):
        #print 'getitem:', key
        return self.source[key]

    def __contains__(self, key):
        #print 'd contains'
        return key in self.source


class ContextStack(ChainMap):

    def __getitem__(self, key):
        if hasattr(self, 'get_%s' % key):
            func = getattr(self, 'get_%s' % key)
            getter = operator.methodcaller('get', key, None)
            values = filter(bool, map(getter, self.maps))
            return func(values)
        else:
            return super(ContextStack, self).__getitem__(key)


'''
class SettingsStack(object):

    def __init__(self, *maps):
        #print '  %s.__init__:' % type(self).__name__
        self.chainmap = ChainMap(*maps)

    def __getattr__(self, key):
        print 'stack.getattr:', key
        if not current_app:
            # if outside an app context, only check the main settings
            # module, otherwise circular references can occur when
            # accessing LocalProxys that end up triggering additional
            # settings lookups
            print '  no app'
            try:
                return self.chainmap.maps[-1][key]
            except KeyError:
                raise AttributeError()

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
            print '  in chainmap', self.chainmap[key]
            if key == 'DIRECTORY_DEPTH':
                for m in self.chainmap.maps:
                    print m, m.__dict__
                    print m.get('DIRECTORY_DEPTH', 'derp')
            return self.chainmap[key]
        else:
            # no value exists
            raise AttributeError()

    def push_ctx(self, ctx):
        print 'push ctx:', len(self.chainmap.maps)
        if len(self.chainmap.maps) > 1:
            assert False
        self.chainmap.maps.insert(0, ctx)
'''

'''
class UserSettingsHolder2(object):
    """
    Holder for user configured settings.
    """
    # SETTINGS_MODULE doesn't make much sense in the manually configured
    # (standalone) case.
    SETTINGS_MODULE = None

    def __init__(self, default_settings):
        """
        Requests for configuration variables not in this class are satisfied
        from the module specified in default_settings (if possible).
        """
        self.__dict__['_deleted'] = set()
        self.default_settings = default_settings

    def __getitem__(self, name):
        print '__getitem:', name
        if name in self._deleted:
            raise KeyError
        if name in self.__dict__:
            return self.__dict__[name]
        return self.default_settings[name]

    def __setitem__(self, name, value):
        self._deleted.discard(name)
        self.__dict__[name] = value

    def __delitem__(self, name):
        self._deleted.add(name)
        del self.__dict__[name]

    def __dir__(self):
        return sorted(
          s for s in list(self.__dict__) + dir(self.default_settings)
          if s not in self._deleted
        )

    def __repr__(self):
        return '<%(cls)s>' % {
          'cls': self.__class__.__name__,
        }

    def is_overridden(self, setting):
        deleted = (setting in self._deleted)
        set_locally = (setting in self.__dict__)
        set_on_default = getattr(self.default_settings, 'is_overridden',
                                 lambda s: False)(setting)
        return deleted or set_locally or set_on_default
'''
