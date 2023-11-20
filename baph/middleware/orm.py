# -*- coding: utf-8 -*-
'''\
:mod:`baph.middleware.orm` -- SQLAlchemy ORM Middleware
=======================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''

from __future__ import absolute_import
from baph.db.orm import ORM


class SQLAlchemyMiddleware(object):
    '''Django middleware which adds an ORM instance to the request object.
    If the request throws an exception, the current SQL transaction is rolled
    back.
    '''

    def process_request(self, request):
        request.orm = ORM.get()

    def process_response(self, request, response):
        #print('process_response:')
        if hasattr(request, 'orm'):
            session = request.orm.sessionmaker()
            try:
                session.flush()
            except:
                session.rollback()
        return response

    def process_exception(self, request, exception):
        #print('process_exception:')
        if hasattr(request, 'orm'):
            session = request.orm.sessionmaker()
            session.rollback()
        return None
