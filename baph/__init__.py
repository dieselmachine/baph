from __future__ import absolute_import
import collections
from functools import wraps
import inspect
import sys


python_version = (sys.version_info.major, sys.version_info.minor)


if python_version > (3, 9):
    import collections.abc
    setattr(collections, 'Callable', collections.abc.Callable)
    setattr(collections, 'Iterable', collections.abc.Iterable)
    setattr(collections, 'Iterator', collections.abc.Iterator)
    setattr(collections, 'Mapping', collections.abc.Mapping)
    setattr(collections, "MutableMapping", collections.abc.MutableMapping)
    setattr(collections, 'Sequence', collections.abc.Sequence)


if python_version > (3, 10):
    inspect.getargspec = inspect.getfullargspec


def replace_settings_class():
    from django import conf
    from baph.conf import settings
    conf.settings = settings


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

    from django.test import testcases

    def connections_support_transactions():
        return False

    testcases.connections_support_transactions = connections_support_transactions


replace_settings_class()
