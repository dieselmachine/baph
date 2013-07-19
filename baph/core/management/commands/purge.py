# -*- coding: utf-8 -*-
from optparse import make_option
import traceback

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style
#from django.core.management.sql import custom_sql_for_model, emit_post_sync_signal
from django.dispatch import Signal
from django.utils.datastructures import SortedDict
from django.utils.importlib import import_module
from sqlalchemy import MetaData, inspect
from sqlalchemy.engine import reflection
from sqlalchemy.schema import CreateSchema, DropSchema, CreateTable, DropTable, DropConstraint, ForeignKeyConstraint, Table, MetaData

from baph.db import connections, Session, DEFAULT_DB_ALIAS
from baph.db.models import Base, signals, get_apps, get_models


post_syncdb = Signal(providing_args=["class", "app", "created_models", 
    "verbosity", "interactive", "db"])

def get_tablename(obj):
    if hasattr(obj, '__table__'):
        " this is a class "
        table = obj.__table__
        schema = table.schema or obj.metadata.bind.url.database
        name = table.name
    elif hasattr(obj, 'schema'):
        " this is a table "
        schema = obj.schema or obj.metadata.bind.url.database
        name = obj.name
    else:
        return None
    return '%s.%s' % (schema, name)


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to purge. '
                'Defaults to the "default" database.'),
    )
    help = "Delete the database tables for all apps in INSTALLED_APPS."

    def handle_noargs(self, **options):
        verbosity = 3 #int(options.get('verbosity'))
        interactive = options.get('interactive')
        show_traceback = options.get('traceback')

        self.style = no_style()

        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_name in settings.INSTALLED_APPS:
            print 'importing mgmt for app_name:', app_name
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
        engine = connections[db]
        inspector = reflection.Inspector.from_engine(engine)
        conn = engine.connect()
        default_db = engine.url.database
        Base.metadata.bind = engine


        existing_schemas = set([s[0] 
            for s in conn.execute('show databases') if s[0]])
        if verbosity >= 1:
            self.stdout.write("Getting existing schemas...\n")
            if verbosity >= 3:
                for schema in existing_schemas:
                    self.stdout.write("\t%s\n" % schema)

        existing_tables = []
        if verbosity >= 1:
            self.stdout.write("Getting existing tables...\n")
        for schema in existing_schemas:
            for name in engine.engine.table_names(schema, connection=conn):
                existing_tables.append('%s.%s' % (schema,name))
                if verbosity >= 3:
                    self.stdout.write("\t%s.%s\n" % (schema,name))    

        existing_models = []
        if verbosity >= 1:
            self.stdout.write("Getting existing models...\n")
        for cls_name, cls in Base._decl_class_registry.items():
            tablename = get_tablename(cls)
            if tablename and tablename in existing_tables:
                existing_models.append(cls)
                if verbosity >= 3:
                    self.stdout.write("\t%s\n" % cls)

        all_tables = []
        if verbosity >= 1:
            self.stdout.write("Getting required tables...\n")
        for table in reversed(Base.metadata.sorted_tables):
            tablename = get_tablename(table)
            all_tables.append(tablename)
            if verbosity >= 3:
                self.stdout.write("\t%s\n" % tablename)

        all_models = []
        if verbosity >= 1:
            self.stdout.write("Getting required models...\n")
        for app in get_apps():
            for model in get_models(app, include_auto_created=True):
                app_name = app.__name__.rsplit('.',1)[0]
                all_models.append( (app_name, model) )
                if verbosity >= 3:
                    self.stdout.write("\t%s.%s\n" % (app_name,model))


        table_manifest = []
        if verbosity >= 1:
            self.stdout.write('Building manifest...\n')
        for app_name, model in all_models:
            tablename = get_tablename(model)
            if tablename not in existing_tables:
                continue
            table_manifest.append( (app_name, model) )
        table_manifest = sorted(table_manifest, key=lambda x: 
            all_tables.index(get_tablename(x[1])))


        metadata = MetaData()
        tbs = []
        all_fks = []
        if verbosity >= 1:
            self.stdout.write("Purging existing tables...\n")
        for app_name, model in table_manifest:
            if verbosity >= 3:
                self.stdout.write("\t%s\n" % get_tablename(model.__table__))
            table_name = model.__table__.name
            if any(t.name == table_name for t in tbs):
                continue
            fks = []
            for fk in inspector.get_foreign_keys(table_name):
                if not fk['name']:
                    continue
                fks.append(ForeignKeyConstraint((), (), name=fk['name']))
            t = Table(table_name, metadata, *fks)
            tbs.append(t)
            all_fks.extend(fks)

        for fkc in all_fks:
            conn.execute(DropConstraint(fkc))

        for table in tbs:
            conn.execute(DropTable(table))
