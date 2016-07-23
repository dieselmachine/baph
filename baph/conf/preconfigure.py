import imp
import inspect
import itertools
import os
import sys


PRECONFIG_MODULE_NAME = 'preconfig'

class BaseOption(object):
  def __init__(self, name, args, default='', choices=None, required=False):
    self.name = name
    self.args = args
    self.default = default
    self.choices = choices
    self.required = required

  @property
  def arg_params(self):
    args = self.args
    kwargs = {
      'metavar': self.name,
      'dest': self.name,
      'default': self.default,
      'choices': self.choices,
      'required': self.required,
    }
    return (args, kwargs)

class ModuleOption(BaseOption):
  def __init__(self, *args, **kwargs):
    self.order = kwargs.pop('order', None)
    super(ModuleOption, self).__init__(*args, **kwargs)
    if self.order is None:
      self.order = self.name

class PackageOption(BaseOption):
  def __init__(self, *args, **kwargs):
    self.base = kwargs.pop('base', 'settings')
    self.prefix = kwargs.pop('prefix', None)
    super(PackageOption, self).__init__(*args, **kwargs)

class Preconfigurator(object):

  def __init__(self):
    self.cmd = os.path.abspath(inspect.stack()[-1][1])
    self.path = os.path.dirname(self.cmd)
    self.packages = []
    self.modules = []
    self.load()

  def load(self):
    try:
      modinfo = imp.find_module(PRECONFIG_MODULE_NAME, [self.path])
      module = imp.load_module(PRECONFIG_MODULE_NAME, *modinfo)
      args = module.PRECONFIG_ARGS
    except Exception:
      args = {}

    for name, data in args.items():
      scope = data.pop('scope', 'module')
      if scope == 'module':
        opt = ModuleOption(name, **data)
        self.modules.append(opt)
      elif scope == 'package':
        opt = PackageOption(name, **data)
        self.packages.append(opt)
      else:
        raise Exception('invalid scope "%s" (must be "package" or "module")'
          % scope)

    self.modules = sorted(self.modules, key=lambda x: x.order)

  @property
  def core_settings(self):
    return self.module_settings + self.package_settings

  @property
  def module_settings(self):
    return [opt.name for opt in self.modules]

  @property
  def package_settings(self):
    return [opt.name for opt in self.packages]

  @property
  def settings_variants(self):
    keys = self.module_settings
    filenames = []
    for i in range(len(keys)):
      for j in itertools.combinations(keys, i+1):
        s = '_'.join('{%s}' % name for name in j)
        filenames.append(s)
    return filenames

  def add_arguments(self, parser):
    for opt in self.modules + self.packages:
      args, kwargs = opt.arg_params
      parser.add_argument(*args, **kwargs)
