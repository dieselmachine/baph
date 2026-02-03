# -*- coding: utf-8 -*-
from __future__ import print_function
from copy import deepcopy
from optparse import make_option
import sys
import traceback

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style
#from django.core.management.sql import custom_sql_for_model, emit_post_sync_signal
from django.dispatch import Signal
from django.utils.datastructures import SortedDict
from django.utils.importlib import import_module
from six.moves import input
from sqlalchemy import MetaData, inspect, create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.schema import (CreateSchema, DropSchema,
  CreateTable, DropTable, DropConstraint,
  ForeignKeyConstraint, Table, MetaData)

from baph.core.management.new_base import BaseCommand
from baph.db import db, DEFAULT_DB_ALIAS
from baph.db.models import get_apps, get_models
from baph.db.orm import ORM
from baph.db.utils import get_tablename
from baph.utils.db import (get_base_session, get_drop_statements)


post_syncdb = Signal(providing_args=["class", "app", "created_models", 
    "verbosity", "interactive", "db"])


class Command(BaseCommand):
  help = "Delete the database tables and schemas for all apps in INSTALLED_APPS."

  def add_arguments(self, parser):
    parser.add_argument(
      '--noinput', action='store_false', dest='interactive',
      default=True,
      help='Tells Django to NOT prompt the user for input of any kind.'
    )
    parser.add_argument(
      '--database', action='store', dest='database',
      default=DEFAULT_DB_ALIAS, help='Nominates a database to purge. '
      'Defaults to the "default" database.'
    )

  def handle(self, **options):
    verbosity = 1 #int(options.get('verbosity'))
    interactive = options.get('interactive')
    show_traceback = options.get('traceback')

    self.style = no_style()

    # Import the 'management' module within each installed app, to register
    # dispatcher events.
    for app_name in settings.INSTALLED_APPS:
      try:
        import_module('.models', app_name)
      except ImportError as exc:
        pass
      try:
        import_module('.management', app_name)
      except ImportError as exc:
        # This is slightly hackish. We want to ignore ImportErrors
        # if the "management" module itself is missing -- but we don't
        # want to ignore the exception if the management module exists
        # but raises an ImportError for some reason. The only way we
        # can do this is to check the text of the exception. Note that
        # we're a bit broad in how we check the text, because different
        # Python implementations may not use the same text.
        # CPython uses the text "No module named management"
        # PyPy uses "No module named myproject.myapp.management"
        msg = exc.args[0]
        if not msg.startswith('No module named') or 'management' not in msg:
          raise

    db = options.get('database')
    orm = ORM.get(db)
    db_info = orm.settings_dict
    is_test_db = db_info.get('TEST', False)
    if not is_test_db:
      print('Database "%s" cannot be purged because it is not a test ' \
            'database.\nTo flag this as a test database, set TEST to ' \
            'True in the database settings.' % db)
      sys.exit()

    if interactive:
      confirm = input('\nYou have requested a purge of database ' \
          '"%s" (%s). This will IRREVERSIBLY DESTROY all data ' \
          'currently in the database, and DELETE ALL TABLES AND ' \
          'SCHEMAS. Are you sure you want to do this?\n\n' \
          'Type "yes" to continue, or "no" to cancel: ' \
          % (db, orm.engine.url))
    else:
      confirm = 'yes'

    if confirm == 'yes':
        drops = get_drop_statements()
        session = get_base_session()
        for drop in drops:
            session.execute(drop)
        session.commit()
        session.bind.dispose()
    else:
      self.stdout.write("Purge cancelled.\n")
