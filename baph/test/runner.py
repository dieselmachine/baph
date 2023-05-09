from copy import deepcopy
import os
import unittest
import sys

from django.conf import settings
from django.test import runner
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm.session import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from baph.core.management import call_command


class DiscoverRunner(runner.DiscoverRunner):

    def setup_databases(self, **kwargs):
        from baph.db.orm import ORM, Base

        orm = ORM.get()

        # determine which schemas we need
        default_schema = orm.engine.url.database
        schemas = set(t.schema or default_schema \
            for t in Base.metadata.tables.values())

        url = deepcopy(orm.engine.url)
        url.database = None
        self.engine = create_engine(url)
        insp = inspect(self.engine)

        # get a list of already-existing schemas
        existing_schemas = set(insp.get_schema_names())

        # if any of the needed schemas exist, do not proceed
        conflicts = schemas.intersection(existing_schemas)
        if conflicts:
            for c in conflicts:
                print('drop schema %s;' % c)
            sys.exit('The following schemas are already present: %s. ' \
                'TestRunner cannot proceeed' % ','.join(conflicts))
        
        # create schemas
        session = Session(bind=self.engine)
        for schema in schemas:
            session.execute(CreateSchema(schema))
        session.commit()
        session.bind.dispose()

        # create tables
        if len(orm.Base.metadata.tables) > 0:
            orm.Base.metadata.create_all(checkfirst=False)

        # generate permissions
        call_command('createpermissions')

        return schemas

    def teardown_databases(self, old_config, **kwargs):
        call_command('purge', interactive=False)
