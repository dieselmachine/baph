from sqlalchemy import inspect
from sqlalchemy.orm.session import Session
from sqlalchemy.schema import (CreateSchema, DropSchema, DropTable,
                               DropConstraint, ForeignKeyConstraint, Table,
                               MetaData)

from baph.db import db


def get_base_session():
    """ returns a session bound to an engine with no schema
        (used for setup/teardown when the default_schema may not exist)
    """
    bind = db.get_base_engine()
    return Session(bind=bind)


def get_default_schema():
    return db.engine.url.database


def get_app_tables():
    """ returns all tables used by the app """
    return db.Base.metadata.tables.values()


def get_app_tablenames():
    """ returns all app table names, with explicit schemas """
    default_schema = get_default_schema()
    return set(['%s.%s' % (table.schema or default_schema, table.name)
                for table in get_app_tables()])


def get_app_schemas():
    """ returns all schemas used by the app """
    tables = get_app_tables()
    schemas = set(table.schema for table in tables)
    schemas.discard(None)
    schemas.add(get_default_schema())
    return schemas


def create_app_schemas():
    """ create all schemas used by the app """
    session = get_base_session()
    for schema in get_app_schemas():
        session.execute(CreateSchema(schema))
    session.commit()
    session.bind.dispose()


def create_app_tables():
    """ creates all tables used by the app """
    tables = get_app_tables()
    if tables:
        db.Base.metadata.create_all(bind=db.engine, checkfirst=False)


def get_existing_schemas():
    """ returns all schemas present on the db """
    bind = db.get_base_engine()
    insp = inspect(bind)
    return set(insp.get_schema_names())


def get_existing_tablenames_for_schema(schema):
    bind = db.get_base_engine()
    insp = inspect(bind)
    return set(['%s.%s' % (schema, table_name)
                for table_name in insp.get_table_names(schema)])

def get_existing_tablenames():
    schemas = get_existing_schemas()
    tablenames = set()
    for schema in schemas:
        tablenames.update(get_existing_tablenames_for_schema(schema))
    return tablenames


def get_existing_fks_for_table(tablename):
    bind = db.get_base_engine()
    insp = inspect(bind)
    schema, name = tablename.split('.')
    return set([fk['name'] for fk in insp.get_foreign_keys(name, schema=schema)
                if fk['name']])


def get_drop_statements():
    """ returns a list of Drop statements needed to clear the db """
    app_schemas = get_app_schemas()
    existing_schemas = get_existing_schemas()
    schemas = app_schemas.intersection(existing_schemas)

    app_tables = get_app_tablenames()
    existing_tables = get_existing_tablenames()
    tables = app_tables.intersection(existing_tables)

    metadata = MetaData()
    db_tables = []
    all_fks = []

    for fullname in tables:
        schema, table_name = fullname.split('.')
        fk_names = get_existing_fks_for_table(fullname)
        fks = [ForeignKeyConstraint((), (), name=fk_name)
               for fk_name in fk_names]
        t = Table(table_name, metadata, *fks, schema=schema)
        db_tables.append(t)
        all_fks.extend(fks)

    drops = []
    drops.extend([DropConstraint(fkc) for fkc in all_fks])
    drops.extend([DropTable(table) for table in db_tables])
    drops.extend([DropSchema(schema) for schema in schemas])
    return drops
