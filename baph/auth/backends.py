# -*- coding: utf-8 -*-
'''\
=========================================================================
:mod:`baph.auth.backends` -- SQLAlchemy backend for Django Authentication
=========================================================================

.. moduleauthor:: Mark Lee <markl@evomediagroup.com>
'''
import django.core.validators

from baph.auth.models import User
from baph.db import Session


class SQLAlchemyBackend(object):
    '''Authentication backend using SQLAlchemy. See
    :setting:`AUTHENTICATION_BACKENDS` for details on
    setting this class as the authentication backend for your project.
    '''

    supports_object_permissions = False
    supports_anonymous_user = True

    def authenticate(self, username=None, password=None, session=None, **kwargs):
        # TODO: Model, login attribute name and password attribute name
        # should be configurable.
        if not session:
            session = Session()
        user = session.query(User) \
                      .filter_by(username=username) \
                      .first()

        if user is None:
            return user
        elif user.check_password(password):
            return user
        else:
            return None

    def get_user(self, user_id, session=None):
        if not session:
            session = Session()
        return session.query(User).get(user_id)
        
class MultiSQLABackend(SQLAlchemyBackend):
    def authenticate(self, identification, password=None, check_password=True):
        session = Session()
        try:
            django.core.validators.validate_email(identification)
            user = session.query(User).filter_by(email=identification).first()
            if not user: return None
        except django.core.validators.ValidationError:
            filters = {User.USERNAME_FIELD: identification}
            user = session.query(User).filter_by(**filters).first()
            if not user: return None
        if check_password:
            if user.check_password(password):
                return user
            return None
        else: return user

