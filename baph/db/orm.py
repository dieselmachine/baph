raise Exception('stop using this')

from baph.db import ORM
orm = ORM.get()
Base = orm.Base
