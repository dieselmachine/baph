from django.test.utils import override_settings as _override

from baph.conf import settings as stack


def get_keys(obj):
    #print '\n\nget_keys:', obj
    #print sorted(obj.keys())
    #for m in obj.maps:
    #    print m, sorted(m.keys())
    try:
        #print sorted(list(obj)), 'LIST'
        return list(obj)
    except TypeError:
        #print sorted(dir(obj)), 'DIR'
        return dir(obj)


class UserSettingsHolder(object):
    SETTINGS_MODULE = None

    def __init__(self, default_settings):
        #print 'holder init', default_settings
        self.__dict__['_deleted'] = set()
        self.default_settings = default_settings

    def __getattr__(self, name):
        #print 'holder.getattr:', name
        if name in self._deleted:
            raise AttributeError
        return getattr(self.default_settings, name)

    def __getitem__(self, name):
        #print 'holder.getitem:', name
        try:
            return getattr(self, name)
        except AttributeError:
            return self.default_settings[name]

    def __setattr__(self, name, value):
        #print 'holder.setattr:', (name, value)
        self._deleted.discard(name)
        return super(UserSettingsHolder, self).__setattr__(name, value)

    def __setitem__(self, name, value):
        #print 'holder.setitem:', (name, value)
        setattr(self, name, value)

    def __delattr__(self, name):
        self._deleted.add(name)
        return super(UserSettingsHolder, self).__delattr__(name)

    def __dir__(self):
        return sorted(
          s for s in list(self.__dict__) + get_keys(self.default_settings)
          if s not in self._deleted
        )

    def __repr__(self):
        return '<%(cls)s>' % {
          'cls': self.__class__.__name__,
        }

    def __contains__(self, name):
        #print 'contains:', name #, name in dir(self)
        #print '  ', self.default_settings, self
        '''
        if name == 'MIDDLEWARE_CLASSES':
            m1 = self.default_settings.maps[0]
            m2 = self.default_settings.maps[1]
            print m1, sorted(m1.keys()), sorted(dir(m1))
            print m2, sorted(m2.keys()), sorted(dir(m2))
            print self[name]
            #print m1[name]
            print '\nM2:', m2[name]
        '''
        return name in dir(self)


class override_settings(_override):
    def __init__(self, name=None, **kwargs):
        self.name = name
        self.options = kwargs

    @property
    def settings(self):
        if self.name is not None:
            return stack.loaders[self.name]
        else:
            return stack

    def enable(self):
        #print 'override enabled'
        override = UserSettingsHolder(self.settings._wrapped)
        for key, new_value in self.options.items():
            setattr(override, key, new_value)
        self.wrapped = self.settings._wrapped
        self.settings._wrapped = override
