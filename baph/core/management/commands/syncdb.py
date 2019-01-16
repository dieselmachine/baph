# -*- coding: utf-8 -*-
import operator

from django.conf import settings
from django.core.management.color import no_style
from django.utils.importlib import import_module
from sqlalchemy import Table
from sqlalchemy.engine.url import make_url
from sqlalchemy.schema import CreateSchema

from baph.core.management.new_base import BaseCommand
from baph.core.management.sql import emit_post_sync_signal
from baph.db import DEFAULT_DB_ALIAS
from baph.db.models import get_apps, get_models
from baph.db.orm import ORM


def get_tablename(obj):
    if hasattr(obj, '__table__'):
        " this is a class "
        table = obj.__table__
        if not isinstance(table, Table):
            # non-table, maybe an aliased construct or view
            return None
        schema = table.schema or obj.metadata.bind.url.database
        name = table.name
    elif hasattr(obj, 'schema'):
        " this is a table "
        schema = obj.schema or obj.metadata.bind.url.database
        name = obj.name
    else:
        return None
    return '%s.%s' % (schema, name)


class Command(BaseCommand):
    '''
    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--no-initial-data', action='store_false', dest='load_initial_data', default=True,
            help='Tells Django not to load any initial data after database synchronization.'),
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to synchronize. '
                'Defaults to the "default" database.'),
    )
    '''
    help = ("Create the database tables for all apps in INSTALLED_APPS whose "
            "tables haven't already been created.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', action='store_false', dest='interactive',
            default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'
        )
        parser.add_argument(
            '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. '
                 'Defaults to the "default" database.'
        )

    def register_dispatchers(self):
        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_name in settings.INSTALLED_APPS:
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
                if (not msg.startswith('No module named')
                        or 'management' not in msg):
                    raise

    def info(self, level, msg):
        if self.verbosity >= level:
            self.stdout.write("%s\n" % msg)

    def ensure_default_schema(self):
        """
        ensure the default_schema is present.
        if missing, it will be created
        """
        if self.default_schema not in self.existing_schemas:
            self.info(1, "Creating default schema %r" % self.default_schema)
            engine = self.orm.get_base_engine()
            engine.execute(CreateSchema(self.default_schema))
            self.existing_schemas.add(self.default_schema)

    def get_existing_schemas(self):
        """
        returns a set of all schemas currently present in the db
        """
        engine = self.orm.get_base_engine()
        conn = engine.connect()
        getter = operator.itemgetter(0)
        schemas = set(map(getter, conn.execute('show databases')))
        if self.verbosity >= 3:
            self.stdout.write("Getting existing schemas...\n")
            for schema in sorted(schemas):
                self.stdout.write("\t%s\n" % schema)
            else:
                self.stdout.write("\tNone\n")
        return schemas

    def get_existing_tables(self):
        engine = self.engine
        conn = engine.connect()
        tables = []
        self.info(1, "Getting existing tables...")
        for schema in self.existing_schemas:
            for name in engine.engine.table_names(schema, connection=conn):
                tables.append('%s.%s' % (schema, name))
                self.info(3, "\t%s.%s" % (schema, name))
        return tables

    def get_existing_models(self):
        models = []
        self.info(1, "Getting existing models...")
        for cls_name, cls in self.Base._decl_class_registry.items():
            tablename = get_tablename(cls)
            if tablename and tablename in self.existing_tables:
                models.append(cls)
                self.info(3, "\t%s" % cls)
        return models

    def get_required_tables(self):
        tables = []
        self.info(1, "Getting required tables...")
        for table in self.Base.metadata.sorted_tables:
            tablename = get_tablename(table)
            tables.append(tablename)
            self.info(3, "\t%s" % tablename)
        return tables

    def get_required_models(self):
        models = []
        self.info(1, "Getting required models...")
        for app in get_apps():
            for model in get_models(app, include_auto_created=True):
                app_name = app.__name__.rsplit('.', 1)[0]
                models.append((app_name, model))
                self.info(3, "\t%s.%s" % (app_name, model.__name__))
        return models

    def build_manifest(self):
        manifest = {
            'schemas': set(),
            'tables': set(),
        }
        self.info(1, 'Building manifest')
        for app_name, model in self.required_models:
            tablename = get_tablename(model)
            if tablename not in self.existing_tables:
                manifest['tables'].add((tablename, app_name, model))
                schema = tablename.rsplit('.', 1)[0]
                if schema not in self.existing_schemas:
                    manifest['schemas'].add(schema)
        manifest['tables'] = sorted(manifest['tables'], key=lambda x:
                                    self.required_tables.index(x[0]))
        return manifest

    def display_manifest(self, manifest):
        self.info(3, "Schema manifest")
        for schema in manifest['schemas']:
            self.info(3, '\t%s' % schema)
        self.info(3, "Model/Table manifest")
        for tablename, app_name, model in manifest['tables']:
            self.info(3, '\t%s.%s (%s)' % (
                app_name, model._meta.object_name, tablename))

    def create_schemas(self, schemas):
        self.info(1, "Creating missing schemas...")
        for schema in schemas:
            self.info(3, "\t%s" % schema)
            self.engine.execute(CreateSchema(schema))
            self.existing_schemas.add(schema)

    def create_tables(self, tables):
        created_models = set()
        to_create = []
        self.info(1, "Creating missing tables...")
        for tablename, app_name, model in tables:
            self.info(3, "\tCreating table for model %s.%s\n"
                      % (app_name, model._meta.object_name))
            if tablename not in self.existing_tables:
                table = model.__table__
                to_create.append(table)
                self.existing_tables.append(tablename)
            self.existing_models.append(model)
            created_models.add(model)
        self.Base.metadata.create_all(bind=self.engine, tables=to_create)
        emit_post_sync_signal(created_models, self.verbosity,
                              self.interactive, self.database)

    def handle(self, **options):
        self.verbosity = options['verbosity']
        self.interactive = options['interactive']
        self.traceback = options['traceback']
        self.database = options['database']
        self.style = no_style()
        self.register_dispatchers()

        self.orm = ORM.get(self.database)
        self.engine = self.orm.engine
        self.Base = self.orm.Base
        self.Base.metadata.bind = self.engine

        self.default_schema = self.engine.url.database
        self.existing_schemas = self.get_existing_schemas()
        self.ensure_default_schema()
        self.existing_tables = self.get_existing_tables()
        self.existing_models = self.get_existing_models()

        self.required_tables = self.get_required_tables()
        self.required_models = self.get_required_models()

        manifest = self.build_manifest()
        if self.verbosity >= 3:
            self.display_manifest(manifest)
        self.create_schemas(manifest['schemas'])
        self.create_tables(manifest['tables'])
