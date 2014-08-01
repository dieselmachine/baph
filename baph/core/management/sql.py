from baph.apps import apps
from baph.db import models
from baph.db.orm import ORM, Base


def emit_post_migrate_signal(created_models, verbosity, interactive, db):
    # Emit the post_sync signal for every application.
    for app_config in apps.get_app_configs():
        if app_config.models_module is None:
            continue
        if verbosity >= 2:
            print("Running post-migrate handlers for application %s" % app_config.label)
        models.signals.post_migrate.send(
            sender=app_config,
            app_config=app_config,
            verbosity=verbosity,
            interactive=interactive,
            using=db)
