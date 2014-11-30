import django.core.validators

from baph.contrib.auth.models import BaseUser, User, Organization
from baph.contrib.auth.registration import settings as auth_settings
from baph.db.orm import ORM


orm = ORM.get()

class MultiSQLAlchemyBackend(object):
    """Backend which auths via username or email"""
    
    def authenticate(self, identification, password=None, check_password=True):
        print 'auth'
        session = orm.sessionmaker()
        org_key = Organization.resource_name.lower() + '_id'
        user = None
        try:
            # if it looks like an email, lookup against the email column
            django.core.validators.validate_email(identification)
            filters = {'email': identification}
            if auth_settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
                filters[org_key] = Organization.get_current_id()
            user = session.query(User).filter_by(**filters).first()
        except django.core.validators.ValidationError:
            # this wasn't an email
            pass
        if not user:
            # email lookup failed, try username lookup if enabled
            if auth_settings.BAPH_AUTH_WITHOUT_USERNAMES:
                # usernames are not valid login credentials
                return None
            filters = {User.USERNAME_FIELD: identification}
            if auth_settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
                filters[org_key] = Organization.get_current_id()
            user = session.query(User).filter_by(**filters).first()
        if not user:
            return None
        if check_password:
            if user.check_password(password):
                print user
                return user
            return None
        else: return user

    def get_user(self, user_id):
        print 'get_user'
        session = orm.sessionmaker()
        return session.query(User).get(user_id)

class MultiSQLAlchemyBackend2(object):
    """Backend which auths via username or email"""
    
    def authenticate(self, identification, password=None, check_password=True):
        print 'auth called'
        session = orm.sessionmaker()
        org_key = Organization.resource_name.lower() + '_id'
        user = None
        try:
            # if it looks like an email, lookup against the email column
            django.core.validators.validate_email(identification)
            filters = {'email': identification}
            auth_cls = getattr(User, 'AUTH_CLASS', User)
            auth = session.query(auth_cls).filter_by(**filters).first()
            print 'found user:', (auth,)
        except django.core.validators.ValidationError:
            # this wasn't an email
            pass

        if not auth:
            # email lookup failed, try username lookup if enabled
            if auth_settings.BAPH_AUTH_WITHOUT_USERNAMES:
                # usernames are not valid login credentials
                return None
            filters = {auth_cls.USERNAME_FIELD: identification}
            if auth_settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
                filters[org_key] = Organization.get_current_id()
            auth = session.query(auth_cls).filter_by(**filters).first()

        if not auth:
            # username lookup failed, no user found
            return None
        if check_password:
            if auth.check_password(password):
                return auth
            return None
        else: return auth

    def get_user(self, user_id):
        print 'get_user'
        session = orm.sessionmaker()
        return session.query(User).get(user_id)

    def get_org_user(self, user_id, org_id):
        print 'get_org_user', user_id, org_id
        session = orm.sessionmaker()
        org_col = getattr(User, Organization.get_column_key())
        user = session.query(User) \
            .filter(org_col==org_id) \
            .filter(User.user_id==user_id) \
            .first()
        print 'user:', user
        return user

