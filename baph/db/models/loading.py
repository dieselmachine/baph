from __future__ import absolute_import
import imp
from django.apps import apps


__all__ = ('get_apps', 'get_app', 'get_models', 'get_model', 'register_models',
        'load_app', 'app_cache_ready')


cache = apps


get_apps = apps.get_apps
get_app_package = apps.get_app_package
get_app_path = apps.get_app_path
get_app_paths = apps.get_app_paths
get_app = apps.get_app
get_models = apps.get_models
get_model = apps.get_model
register_models = apps.register_models
load_app = apps.load_app
app_cache_ready = apps.app_cache_ready
#unregister_models = apps.unregister_models


def get_app_errors():
    try:
        return apps.app_errors
    except AttributeError:
        apps.app_errors = {}
        return apps.app_errors
