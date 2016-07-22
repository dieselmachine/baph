import imp
import inspect
import itertools
import os
import sys


PRECONFIG_MODULE_NAME = 'preconfig'

class Preconfigurator(object):

  modules = []
  packages = []
  loaded = False

  def __init__(self):
    self.cmd = os.path.abspath(inspect.stack()[-1][1])
    self.path = os.path.dirname(self.cmd)

  def load(self):
    if self.loaded:
      return
    try:
      modinfo = imp.find_module(PRECONFIG_MODULE_NAME, [self.path])
      module = imp.load_module(PRECONFIG_MODULE_NAME, *modinfo)
      args = module.PRECONFIG_ARGS
    except Exception:
      args = {}

    modules = {}
    packages = []
    for name, data in args.items():
      scope = data.pop('scope', 'module')
      if scope not in ('module', 'package'):
        raise Exception('invalid scope "%s" (must be "package" or "module")'
          % data['scope'])
      data['metavar'] = name
      data['dest'] = name
      if scope == 'package':
        packages.append(data)
        continue
      order = data.pop('order', name)
      modules[order] = data

    self.modules = [module for order, module in sorted(modules.items())]
    self.packages = packages
    self.loaded = True

  def get_settings_names(self):
    self.load()
    return [item['metavar'] for item in self.modules + self.packages]

  @property
  def module_settings(self):
    self.load()
    return [item['metavar'] for item in self.modules]

  @property
  def package_settings(self):
    self.load()
    return [item['metavar'] for item in self.packages]

  def add_arguments(self, parser):
    self.load()
    for item in self.modules + self.packages:
      item = item.copy()
      args = item.pop('args')
      parser.add_argument(*args, **item)

  @property
  def settings_files(self):
    self.load()
    keys = [item['metavar'] for item in self.modules]
    filenames = ['settings']
    for i in range(len(keys)):
      for j in itertools.combinations(keys, i+1):
        s = '_'.join('{%s}' % name for name in j)
        filenames.append(s)
    return filenames