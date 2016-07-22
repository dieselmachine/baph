from baph.conf import settings
from baph.core import signals
from baph.core.exceptions import ImproperlyConfigured
#from baph.db import (ConnectionHandler, ConnectionRouter,
#                       DefaultConnectionProxy, DatabaseError, IntegrityError)

#from baph.db.utils import EngineHandler, DEFAULT_DB_ALIAS


#__all__ = ('ORM', 'DEFAULT_DB_ALIAS', 'engines', 'EngineHandler',
#    'DatabaseError', 'IntegrityError', )
# 'connection', 'connections', 'router', 
'''
ORM = EngineHandler(settings.DATABASES)

connections = ConnectionHandler()

router = ConnectionRouter()

connection = DefaultConnectionProxy()
'''