import importlib
import itertools
import os
import sys
import time

from baph.conf import global_settings
from baph.conf.preconfigure import Preconfigurator
from baph.core.exceptions import ImproperlyConfigured
from baph.utils.functional import LazyObject, empty, cached_property
from baph.utils.termcolors import make_style


ENVIRONMENT_VARIABLE = "FLASK_SETTINGS_MODULE"
APPEND_SETTINGS = (
  'TEMPLATE_CONTEXT_PROCESSORS',
  'MIDDLEWARE_CLASSES',
  'JINJA2_FILTERS',
)
PREPEND_SETTINGS = (
  'INSTALLED_APPS',
  'TEMPLATE_DIRS',
)

success_msg = make_style(fg='green')
notice_msg = make_style(fg='yellow')
error_msg = make_style(fg='red')
info_msg = make_style(fg='blue')

class LazySettings(LazyObject):
    """
    A lazy proxy for either global Django settings or a custom settings object.
    The user can manually configure settings prior to using them. Otherwise,
    Django uses the settings module pointed to by DJANGO_SETTINGS_MODULE.
    """
    def _setup(self, name=None):
        """
        Load the settings module pointed to by the environment variable. This
        is used the first time we need any settings at all, if the user has not
        previously configured the settings manually.
        """
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        if not settings_module:
            desc = ("setting %s" % name) if name else "settings"
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (desc, ENVIRONMENT_VARIABLE))

        self._wrapped = Settings(settings_module)

    def __repr__(self):
        # Hardcode the class name as otherwise it yields 'Settings'.
        if self._wrapped is empty:
            return '<LazySettings [Unevaluated]>'
        return '<LazySettings "%(settings_module)s">' % {
            'settings_module': self._wrapped.SETTINGS_MODULE,
        }

    def __getattr__(self, name):
        if self._wrapped is empty:
            self._setup(name)
        return getattr(self._wrapped, name)

    def configure(self, default_settings=global_settings, **options):
        """
        Called to manually configure the settings. The 'default_settings'
        parameter sets where to retrieve any unspecified values from (its
        argument must support attribute access (__getattr__)).
        """
        if self._wrapped is not empty:
            raise RuntimeError('Settings already configured.')
        holder = UserSettingsHolder(default_settings)
        for name, value in options.items():
            setattr(holder, name, value)
        self._wrapped = holder

    @property
    def configured(self):
        """
        Returns True if the settings have already been configured.
        """
        print 'configured?'
        return self._wrapped is not empty

class BaseSettings(object):
  """
  Common logic for settings whether set by a module or by the user.
  """
  def __setattr__(self, name, value):
    if name in ("MEDIA_URL", "STATIC_URL") and value \
            and not value.endswith('/'):
      raise ImproperlyConfigured("If set, %s must end with a slash"
            % name)
    object.__setattr__(self, name, value)

class Settings(BaseSettings):
  def __init__(self, settings_module):
    print 'Settings.__init__:', settings_module
    
    self.settings = importlib.import_module(settings_module)
    self.file = self.settings.__file__
    if os.path.basename(self.file) in ('__init__.py', '__init__.pyc'):
      self.package = settings_module
    else:
      self.package = settings_module.rsplit('.', 1)[0]
    self.sources = {}
    self.messages = []

    self.process_environment_vars()

    # update this dict from global settings (but only for ALL_CAPS settings)
    for setting in dir(global_settings):
      if setting.isupper():
        setattr(self, setting, getattr(global_settings, setting))

    self.import_base_settings()
    self.load_package_settings(self.package)

    # store the settings module in case someone later cares
    self.SETTINGS_MODULE = settings_module

    mod = importlib.import_module(self.SETTINGS_MODULE)

    tuple_settings = (
      "INSTALLED_APPS",
      "TEMPLATE_DIRS",
      "LOCALE_PATHS",
    )
    self._explicit_settings = set()
    for setting in dir(mod):
      if setting.isupper():
        setting_value = getattr(mod, setting)

        if (setting in tuple_settings and
                not isinstance(setting_value, (list, tuple))):
          raise ImproperlyConfigured(
            "The %s setting must be a list or a tuple. " % setting)
        setattr(self, setting, setting_value)
        self._explicit_settings.add(setting)

    if not self.SECRET_KEY:
      raise ImproperlyConfigured("The SECRET_KEY setting must not be empty.")

    if hasattr(time, 'tzset') and self.TIME_ZONE:
      # When we can, attempt to validate the timezone. If we can't find
      # this file, no check happens and it's harmless.
      zoneinfo_root = '/usr/share/zoneinfo'
      if (os.path.exists(zoneinfo_root) and not
          os.path.exists(os.path.join(zoneinfo_root,
            *(self.TIME_ZONE.split('/'))))):
        raise ValueError("Incorrect timezone setting: %s" % self.TIME_ZONE)
      # Move the time zone info into os.environ. See ticket #2315 for why
      # we don't do this unconditionally (breaks Windows).
      os.environ['TZ'] = self.TIME_ZONE
      time.tzset()

  @cached_property
  def core_settings(self):
    preconfig = Preconfigurator()
    return preconfig.get_settings_names()

  @cached_property
  def module_settings(self):
    preconfig = Preconfigurator()
    return preconfig.module_settings

  @cached_property
  def package_settings(self):
    preconfig = Preconfigurator()
    return preconfig.package_settings

  def is_overridden(self, setting):
    return setting in self._explicit_settings

  def __repr__(self):
    return '<%(cls)s "%(settings_module)s">' % {
      'cls': self.__class__.__name__,
      'settings_module': self.SETTINGS_MODULE,
    }

  def settings_files(self, suffixes=None):
    preconfig = Preconfigurator()
    filenames = preconfig.settings_files
    params = {setting: getattr(self, setting)
      for setting in self.core_settings}

    filenames = [filename.format(**params) for filename in filenames]
    if suffixes is not None:
      filenames = itertools.product(filenames, [''] + list(suffixes))
      filenames = map(''.join, filenames)
    return filenames

  def add_message(self, msg):
    """
    Pushes a message onto the stack.
    """
    self.messages.append(msg)

  def flush_messages(self):
    """
    Flushes accumulated messages to the screen
    """
    while self.messages:
      print(self.messages.pop(0))

  def set_setting(self, setting, value, source):
    """
    Handles the setting and overriding of settings
    """
    if setting in self.core_settings:
      # special handling for core vars
      if hasattr(self, setting):
        # do not allow overriding of existing values
        raise ImproperlyConfigured(
          'Error setting %s.%s (previously declared in %s)'
          % (source, setting, self.sources[setting]))
      # track where this came from so we can display the source
      self.sources[setting] = source
      self.add_message('    %s set to %s' % (setting, value))

    if not hasattr(self, setting):
      # first occurence - set the current value as-is
      pass
    elif setting in APPEND_SETTINGS:
      # append the value to the existing value
      value = getattr(self, setting) + value
    elif setting in PREPEND_SETTINGS:
      # prepent the value to the existing value
      value = value + getattr(self, setting)
    else:
      # override the existing value
      pass

    setattr(self, setting, value)

  def process_environment_vars(self):
    print info_msg('\n*** Initializing settings environment ***')
    for setting in self.core_settings:
      if os.environ.get(setting, None):
        # found a valid value in the environment, save to settings
        setting_value = os.environ[setting]
        self.set_setting(setting, setting_value, 'os.environ')
    
    # ensure required params were set in manage.py/wsgi.py
    for setting in self.module_settings:
      if not getattr(self, setting, None):
        sys.tracebacklimit = 0 # no traceback needed for this error
        raise ImproperlyConfigured(
          'setting "%s" not found in environment' % setting)

    self.flush_messages()

  def import_base_settings(self):
    settings_module = os.environ[ENVIRONMENT_VARIABLE]
    if settings_module != self.package:
      # settings being called via another settings file
      # we might need some values from there
      self.load_module_settings(settings_module)

  def merge_settings(self, mod):
    """
    Merges specified module's settings into current settings
    """
    for setting in dir(mod):
      if setting != setting.upper():
        # ignore anything that isn't uppercase
        continue
      setting_value = getattr(mod, setting)
      self.set_setting(setting, setting_value, mod.__name__)

  def load_package_settings(self, package):
    """
    Attempts to load each module from SETTINGS_MODULES from the given package
    """
    print info_msg('\n*** Initializing %s settings ***' % package)
    modules = self.settings_files(suffixes=['_local'])
    modules = map('.'.join, itertools.product([package], modules))
    for mod in modules:
      self.load_module_settings(mod)

  def load_module_settings(self, module):
    """
    Loads a single settings module
    """
    msg = 'loading %s' % module
    print msg.ljust(64),

    if module.startswith(self.package + '.'):
      # import locally if the module is in the base settings dir
      module = module.replace(self.package, '', 1)
    #print 'module:', module

    try:
      if module in sys.modules:
        mod = sys.modules[module]
      else:
        mod = importlib.import_module(module, package=self.package)
      self.merge_settings(mod)
      print success_msg('LOADED')
    except ImportError:
      print notice_msg('NOT FOUND')
    except:
      print error_msg('FAILED')
      raise
    self.flush_messages()

class UserSettingsHolder(BaseSettings):
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

    def __getattr__(self, name):
        if name in self._deleted:
            raise AttributeError
        return getattr(self.default_settings, name)

    def __setattr__(self, name, value):
        self._deleted.discard(name)
        super(UserSettingsHolder, self).__setattr__(name, value)

    def __delattr__(self, name):
        self._deleted.add(name)
        if hasattr(self, name):
            super(UserSettingsHolder, self).__delattr__(name)

    def __dir__(self):
        return list(self.__dict__) + dir(self.default_settings)

    def is_overridden(self, setting):
        deleted = (setting in self._deleted)
        set_locally = (setting in self.__dict__)
        set_on_default = getattr(self.default_settings, 'is_overridden', lambda s: False)(setting)
        return (deleted or set_locally or set_on_default)

    def __repr__(self):
        return '<%(cls)s>' % {
            'cls': self.__class__.__name__,
        }

settings = LazySettings()