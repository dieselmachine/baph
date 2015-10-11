from sqlalchemy.orm.mapper import configure_mappers

def setup():
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the app registry.
    """
    from baph.apps import apps
    from django.conf import settings
    from django.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
    apps.populate(settings.INSTALLED_APPS)
    configure_mappers()

    # hackery to fool django into not breaking during translation activation
    from django.apps import apps as django_apps
    django_apps.populate([])
