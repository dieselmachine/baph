from __future__ import absolute_import
import collections
from functools import wraps
import inspect
import sys


if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec


if not hasattr(collections, 'Iterator'):
    import collections.abc
    setattr(collections, 'Iterator', collections.abc.Iterator)
    setattr(collections, 'Iterable', collections.abc.Iterable)
    setattr(collections, 'Sequence', collections.abc.Sequence)
    setattr(collections, 'Mapping', collections.abc.Mapping)
    setattr(collections, "MutableMapping", collections.abc.MutableMapping)


def replace_settings_class():
    from django import conf
    from baph.conf import settings
    conf.settings = settings


def apply_patches():
    import os
    from importlib import import_module

    patch_dir = os.path.join(os.path.dirname(__file__), 'patches')
    for mod_name in os.listdir(patch_dir):
        filename = os.path.join(patch_dir, mod_name)
        with open(filename, 'rt') as fp:
            src = fp.read()
        code = compile(src, filename, 'exec')
        mod = import_module(mod_name)
        exec(code, mod.__dict__)


class Temp(object):
    def __init__(self, entering, exiting):
        self.entering = entering
        self.exiting = exiting

    def __enter__(self):
        self.entering()

    def __exit__(self, exc_type, exc_value, traceback):
        self.exiting(exc_type)

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return inner


def commit_on_success():
    def entering():
        pass

    def exiting(exc_type):
        pass

    return Temp(entering, exiting)


def setup():
    from baph.conf import settings
    from django.db import transaction

    transaction.commit_on_success = commit_on_success


    from django.apps import apps
    apps.populate(settings.INSTALLED_APPS)

    from baph.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

    #from baph.utils.module_loading import module_has_submodule
    #from django.utils import module_loading
    #from django.apps import config


    #module_loading.module_has_submodule = module_has_submodule
    #config.module_has_submodule = module_has_submodule


    from django.test import testcases

    def connections_support_transactions():
        return False

    testcases.connections_support_transactions = connections_support_transactions


replace_settings_class()
apply_patches()
