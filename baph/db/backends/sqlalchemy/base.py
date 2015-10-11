from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.validation import BaseDatabaseValidation
from django.db.backends.utils import CursorWrapper
from django.conf import settings
from django.utils.functional import cached_property
from sqlalchemy import create_engine, exc
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session, sessionmaker

from baph.db.models.base import Model


class Database(object):
    
    @classmethod
    def connect(cls, **conn_params):
        engine = create_engine()
        assert False
        return engine.raw_connection()

    DataError = exc.DataError
    OperationalError = exc.OperationalError
    IntegrityError = exc.IntegrityError
    InternalError = exc.InternalError
    ProgrammingError = exc.ProgrammingError
    NotSupportedError = exc.NotSupportedError
    DatabaseError = exc.DatabaseError
    InterfaceError = exc.InterfaceError
    Error = type(b'Error', (exc.DBAPIError,), {})

class DatabaseOperations(BaseDatabaseOperations):
    pass

class DatabaseWrapper(BaseDatabaseWrapper):
    # BC - remove when orm.Base is gone
    Base = Model
    vendor = 'sqlalchemy'
    Database = Database
    # This dictionary maps Field objects to their associated MySQL column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__ before being output.
    # If a column type is set to None, it won't be included in the output.
    _data_types = {
        'AutoField': 'integer AUTO_INCREMENT',
        'BinaryField': 'longblob',
        'BooleanField': 'bool',
        'CharField': 'varchar(%(max_length)s)',
        'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
        'DateField': 'date',
        'DateTimeField': 'datetime',
        'DecimalField': 'numeric(%(max_digits)s, %(decimal_places)s)',
        'DurationField': 'bigint',
        'FileField': 'varchar(%(max_length)s)',
        'FilePathField': 'varchar(%(max_length)s)',
        'FloatField': 'double precision',
        'IntegerField': 'integer',
        'BigIntegerField': 'bigint',
        'IPAddressField': 'char(15)',
        'GenericIPAddressField': 'char(39)',
        'NullBooleanField': 'bool',
        'OneToOneField': 'integer',
        'PositiveIntegerField': 'integer UNSIGNED',
        'PositiveSmallIntegerField': 'smallint UNSIGNED',
        'SlugField': 'varchar(%(max_length)s)',
        'SmallIntegerField': 'smallint',
        'TextField': 'longtext',
        'TimeField': 'time',
        'UUIDField': 'char(32)',
    }

    @cached_property
    def data_types(self):
        return self._data_types

    def __init__(self, *args, **kwargs):
        print 'db wrapper init'
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self._engine = None
        self._sessionmaker = None
        self.ops = DatabaseOperations(self)

    @cached_property
    def engine(self):
        conn_params = self.get_connection_params().copy()
        engine_options = conn_params.pop('engine_options', {})
        url = URL(**conn_params)
        print 'url:', url
        return create_engine(url, **engine_options)

    @cached_property
    def sessionmaker(self):
        session_factory = sessionmaker(bind=self.engine, autoflush=False) 
        return scoped_session(session_factory)

    def session(self):
        return self.sessionmaker()


    def get_connection_params(self):
        settings_dict = self.settings_dict
        kwargs = {}
        if settings_dict['USER']:
            kwargs['username'] = settings_dict['USER']
        if settings_dict['NAME']:
            kwargs['database'] = settings_dict['NAME']
        if settings_dict['PASSWORD']:
            kwargs['password'] = settings_dict['PASSWORD']
        if settings_dict['HOST']:
            kwargs['host'] = settings_dict['HOST']
        if settings_dict['PORT']:
            kwargs['port'] = int(settings_dict['PORT'])
        if settings_dict['DRIVERNAME']:
            kwargs['drivername'] = settings_dict['DRIVERNAME']
        if settings_dict['OPTIONS']:
            kwargs['query'] = settings_dict['OPTIONS']
        if settings_dict['ENGINE_OPTIONS']:
            kwargs['engine_options'] = settings_dict['ENGINE_OPTIONS']
        return kwargs

    def get_new_connection(self, conn_params):
        conn = self.engine.connect()
        return conn

    def init_connection_state(self):
        cursor = self.cursor()

    def create_cursor(self):
        cursor = self.connection._Connection__connection.cursor()
        return cursor

    def _rollback(self):
        try:
            BaseDatabaseWrapper._rollback(self)
        except Database.NotSupportedError:
            pass

    def _set_autocommit(self, autocommit):
        with self.wrap_database_errors:
            self.connection.execution_options(autocommit=autocommit)

    def disable_constraint_checking(self):
        """
        Disables foreign key checks, primarily for use in adding rows with 
        forward references. Always returns True, to indicate constraint checks
        need to be re-enabled.
        """
        self.cursor().execute('SET foreign_key_checks=0')
        return True

    def enable_constraint_checking(self):
        """
        Re-enable foreign key checks after they have been disabled.
        """
        # Override needs_rollback in case constraint_checks_disabled is
        # nested inside transaction.atomic.
        self.needs_rollback, needs_rollback = False, self.needs_rollback
        try:
            self.cursor().execute('SET foreign_key_checks=1')
        finally:
            self.needs_rollback = needs_rollback
