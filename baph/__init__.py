def setup():
    from baph.apps import apps
    from baph.conf import settings
    from baph.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
    apps.populate(settings.INSTALLED_APPS)


def replace_settings_class():
    from django import conf
    from baph.conf import settings
    conf.settings = settings


def replace_wsgi_handler():
    """
    django.test.testcases line 1084 has a hardcoded call to the django
    WSGIHandler, so we need to replace that in order to have testcases
    call our handler
    """
    from django.core.handlers import wsgi
    from baph.core.handlers.wsgi import WSGIHandler
    wsgi.WSGIHandler = WSGIHandler


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


replace_settings_class()
replace_wsgi_handler()
apply_patches()
