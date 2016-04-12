# -*- coding: utf-8 -*-
from datetime import datetime
import hashlib
from oauth import oauth
import random
import urllib
import uuid

from django.conf import settings
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable)
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.datastructures import SortedDict
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (relationship, backref, object_session,
    RelationshipProperty, clear_mappers)

from baph.contrib.auth.mixins import UserPermissionMixin
from baph.contrib.auth.registration import settings as auth_settings
from baph.db.models.base import Model as Base
from baph.db.models.manager import Manager
from baph.db.types import UUID, Dict, List
from baph.utils.strings import random_string
from baph.utils.importing import remove_class
import inspect, sys


AUTH_USER_FIELD_TYPE = getattr(settings, 'AUTH_USER_FIELD_TYPE', 'UUID')
AUTH_USER_FIELD = UUID if AUTH_USER_FIELD_TYPE == 'UUID' else Integer
PERMISSION_TABLE = getattr(settings, 'BAPH_PERMISSION_TABLE',
                            'baph_auth_permissions')
UNUSABLE_PASSWORD = '!'

def _generate_user_id_column():
    if AUTH_USER_FIELD_TYPE != 'UUID':
        return Column(AUTH_USER_FIELD, primary_key=True)
    return Column(UUID, primary_key=True, default=uuid.uuid4)

def update_last_login(sender, user, **kwargs):
    """
    A signal receiver which updates the last_login date for
    the user logging in.
    """
    user.last_login = datetime.now()
    user.save(update_fields=['last_login'])
user_logged_in.connect(update_last_login)

def get_or_fail(codename):
    session = orm.sessionmaker()
    try:
        perm = session.query(Permission).filter_by(codename=codename).one()
    except:
        raise ValueError('%s is not a valid permission codename' % codename)
    return PermissionAssociation(permission=perm)

def string_to_model(string):
    if string in orm.Base._decl_class_registry:
        return orm.Base._decl_class_registry[string]
    elif string.title() in Base._decl_class_registry:
        return orm.Base._decl_class_registry[string.title()]
    else:
        # this string doesn't match a resource
        return None


# permission classes

class Permission(Base):
    __tablename__ = PERMISSION_TABLE
    __table_args__ = {
        'info': {'preserve_during_flush': True},
        }

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100))
    codename = Column(String(100), unique=True)
    resource = Column(String(50))
    action = Column(String(16))
    key = Column(String(100))
    value = Column(String(50))

    def __unicode__(self):
        return unicode(str(self))

    def __str__(self):
        return self.name
        
    def __repr__(self):
        return '<Permission: %s (%s) %s:%s, %s=%s>' % (
            self.name, self.codename, self.resource, self.action, self.key, self.value)

# organization models

class AbstractBaseOrganization(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    @classmethod
    def get_relation_key(cls):
        return cls._meta.model_name

    @classmethod
    def get_column_key(cls):
        return '%s_id' % cls.get_relation_key()

    @classmethod
    def get_current(cls, request=None):
        raise ImproperlyConfigured('get_current must be defined on the '
            'custom Organization model')

    @classmethod
    def get_from_request(cls, request):
        raise ImproperlyConfigured('get_from_request must be defined on the '
            'custom Organization model')

    @classmethod
    def get_current_id(cls, request=None):
        org = cls.get_current(request=request)
        if not org:
            return None
        if isinstance(org, dict):
            return org['id']
        else:
            return org.id

    @classmethod
    def get_column_key(cls):
        return cls._meta.model_name+'_id'

    @classmethod
    def get_relation_key(cls):
        return cls._meta.model_name

class BaseOrganization(AbstractBaseOrganization):
    __tablename__ = 'baph_auth_organizations'
    __requires_subclass__ = True
    name = Column(Unicode(200), nullable=False)

class Organization(BaseOrganization):
    class Meta:
        swappable = 'BAPH_ORGANIZATION_MODEL'

# group models

class AbstractBaseGroup(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    context = Column(Dict)

    users = association_proxy('user_groups', 'user',
        creator=lambda v: UserGroup(user=v))
    permissions = association_proxy('permission_assocs', 'permission')
    codenames = association_proxy('permission_assocs', 'codename',
        creator=get_or_fail)

class BaseGroup(AbstractBaseGroup):
    __tablename__ = 'baph_auth_groups'
    __requires_subclass__ = True
    name = Column(Unicode(100))

class Group(BaseGroup):
    class Meta:
        swappable = 'BAPH_GROUP_MODEL'

if not hasattr(Group, Organization.get_column_key()):
    # add the org fk if not declared on the group class
    col = Column(Integer, ForeignKey(Organization.id), index=True)
    setattr(BaseGroup, Organization.get_column_key(), col)

if not hasattr(Group, Organization.get_relation_key()):
    # add the org relation if it wasn't declared on the group class
    rel = RelationshipProperty(Organization,
        backref=Group._meta.model_name_plural,
        foreign_keys=[getattr(BaseGroup, Organization.get_column_key())])
    setattr(Group, Organization.get_relation_key(), rel)


# user models

class AnonymousUser(object):
    id = None
    email = None
    username = ''
    is_staff = False
    is_active = False
    is_superuser = False
    
    def is_anonymous(self):
        return True

    def is_authenticated(self):
        return False

    def has_resource_perm(self, resource):
        return False
    
    def has_perm(self, resource, action, filters=None):
        return False

class UserManager(Manager):

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the address by lowercasing the domain part of the email
        address.
        """
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = '@'.join([email_name, domain_part.lower()])
        return email

    def make_random_password(self, length=10,
                             allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                           'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                           '23456789'):
        """
        Generates a random password with the given length and given
        allowed_chars. Note that the default value of allowed_chars does not
        have "I" or "O" or letters and digits that look similar -- just to
        avoid confusion.
        """
        return get_random_string(length, allowed_chars)

    def _create_user(self, username, email, password, **extra_fields):
        #print '_create_user:', cls, username, email, password
        if not getattr(settings, 'BAPH_AUTH_WITHOUT_USERNAMES', False) and not username:
            raise ValueError('The given username must be set')
        if not any(f in extra_fields for f in (Organization.get_column_key(),
                                              Organization.get_relation_key())):
            # organization was not provided, try .get_current_id if available
            try:
                org_id = Organization.get_current_id()
                extra_fields[Organization.get_column_key()] = org_id
            except ImproperlyConfigured as e:
                # get_current is not defined, org assignment is manual
                pass
            except Exception as e:
                # No idea what caused this error
                raise

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(username, email, password, **extra_fields)


class AbstractBaseUser(Base, UserPermissionMixin):
    __abstract__ = True
    id = _generate_user_id_column()
    email = Column(String(settings.EMAIL_FIELD_LENGTH), index=True,
                    nullable=False)
    password = Column(String(256), nullable=False)
    last_login = Column(DateTime, default=datetime.now, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    date_joined = Column(DateTime, default=datetime.now, nullable=False)

    permissions = association_proxy('permission_assocs', 'permission')
    codenames = association_proxy('permission_assocs', 'codename',
                                  creator=get_or_fail)

    # this is to allow the django password reset token generator to work
    @property
    def pk(self):
        return self.id

    def get_username(self):
        "Return the identifying username for this User"
        return getattr(self, self.USERNAME_FIELD)

    def is_anonymous(self):
        '''Always returns :const:`False`. This is a way of comparing
        :class:`User` objects to anonymous users.
        '''
        return False

    def is_authenticated(self):
        '''Tells if a user's authenticated. Always :const:`True` for this
        class.
        '''
        return True

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
        return check_password(raw_password, self.password, setter)

    def has_usable_password(self):
        '''Determines whether the user has a password.'''
        return self.password != UNUSABLE_PASSWORD

    def set_unusable_password(self):
        '''Sets a password value that will never be a valid hash.'''
        self.password = UNUSABLE_PASSWORD

    # from UserManager




class BaseUser(AbstractBaseUser):
    __tablename__ = 'auth_user'
    __requires_subclass__ = True
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    username = Column(Unicode(75), 
        nullable=auth_settings.BAPH_AUTH_WITHOUT_USERNAMES, index=True)
    first_name = Column(Unicode(30))
    last_name = Column(Unicode(30))

    def email_user(self, subject, message, from_email=None, **kwargs):
        '''Sends an e-mail to this User.'''
        from django.core.mail import send_mail
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_absolute_url(self):
        '''The absolute path to a user's profile.

        :rtype: :class:`str`
        '''
        return '/users/%s/' % urllib.quote(smart_str(self.username))

    def get_full_name(self):
        '''Retrieves the first_name plus the last_name, with a space in
        between and no leading/trailing whitespace.
        '''
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def save(self, update_fields=[], **kwargs):
        session = object_session(self)
        if not session:
            session = orm.sessionmaker()
            session.add(self)
        session.commit()

class User(BaseUser):
    class Meta:
        swappable = 'BAPH_USER_MODEL'

if not hasattr(User, Organization.get_column_key()):
    col = Column(Integer, ForeignKey(Organization.id), index=True)
    setattr(BaseUser, Organization.get_column_key(), col)

if not hasattr(User, Organization.get_relation_key()):
    # add the org relation if it wasn't declared on the user class
    rel = RelationshipProperty(Organization,
        backref=User._meta.model_name_plural,
        foreign_keys=[
            getattr(User, Organization.get_column_key()),
            ])
    setattr(User, Organization.get_relation_key(), rel)

if auth_settings.BAPH_AUTH_UNIQUE_WITHIN_ORG:
    args = [col_key]
else:
    args = []

con = UniqueConstraint(*(args+['email']))
BaseUser.__table__.append_constraint(con)

if not auth_settings.BAPH_AUTH_WITHOUT_USERNAMES:
    con = UniqueConstraint(*(args+[User.USERNAME_FIELD]))
    BaseUser.__table__.append_constraint(con)


# association classes

class UserGroup(Base):
    '''User groups'''
    __tablename__ = 'baph_auth_user_groups'
    __table_args__ = (
        Index('idx_group_context', 'group_id', 'key', 'value'),
        Index('idx_context', 'key', 'value'),
        )

    class Meta:
        permission_parents = ['user']
        permission_handler = 'user'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    group_id = Column(Integer, ForeignKey(Group.id), nullable=False)
    key = Column(String(32))
    value = Column(String(32))

if not hasattr(User, 'user_groups'):
    rel = RelationshipProperty(UserGroup,
        backref='user',
        foreign_keys=[UserGroup.user_id])
    setattr(User, 'user_groups', rel)

if not hasattr(Group, 'user_groups'):
    rel = RelationshipProperty(UserGroup,
        backref='group',
        foreign_keys=[UserGroup.group_id])
    setattr(Group, 'user_groups', rel)

if not hasattr(UserGroup, Organization.get_column_key()):
    col = Column(Integer, ForeignKey(Organization.id), index=True)
    setattr(UserGroup, Organization.get_column_key(), col)

if not hasattr(UserGroup, Organization.get_relation_key()):
    rel = RelationshipProperty(Organization,
        backref=UserGroup._meta.model_name_plural,
        foreign_keys=[getattr(UserGroup, Organization.get_column_key())])
    setattr(UserGroup, Organization.get_relation_key(), rel)


class PermissionAssociation(Base):
    __tablename__ = PERMISSION_TABLE + '_assoc'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(BaseUser.id))
    group_id = Column(Integer, ForeignKey(Group.id))
    perm_id = Column(Integer, ForeignKey(Permission.id), nullable=False)
    fields = Column(List)

    auth = relationship(BaseUser, backref=backref('permission_assocs',
        cascade='all, delete-orphan'))
    group = relationship(Group, backref=backref('permission_assocs',
        cascade='all, delete-orphan'))
    permission = relationship(Permission, lazy='joined')

    codename = association_proxy('permission', 'codename')

if not hasattr(PermissionAssociation, Organization.get_column_key()):
    col = Column(Integer, ForeignKey(Organization.id), index=True)
    setattr(PermissionAssociation, Organization.get_column_key(), col)

if not hasattr(PermissionAssociation, Organization.get_relation_key()):
    rel = RelationshipProperty(Organization,
        backref=PermissionAssociation._meta.model_name_plural,
        foreign_keys=[
            getattr(PermissionAssociation, Organization.get_column_key()),
            ])
    setattr(PermissionAssociation, Organization.get_relation_key(), rel)

if not hasattr(PermissionAssociation, 'user'):
    rel = RelationshipProperty(User, backref='permission_assocs',
        foreign_keys=[
            getattr(PermissionAssociation, Organization.get_column_key()),
            getattr(PermissionAssociation, 'user_id'),
            ],
        primaryjoin="and_("
            "PermissionAssociation.client_id==User.client_id,"
            "PermissionAssociation.user_id==User.user_id)",
        )
    setattr(PermissionAssociation, 'user', rel)

table_args = getattr(PermissionAssociation, '__table_args__', tuple())

fk = ForeignKeyConstraint(
    [getattr(PermissionAssociation, Organization.get_column_key()),
        PermissionAssociation.user_id],
    [getattr(User, Organization.get_column_key()), User.user_id],
    )

uq = UniqueConstraint(
    getattr(PermissionAssociation, Organization.get_column_key()),
    PermissionAssociation.user_id,
    PermissionAssociation.group_id,
    PermissionAssociation.perm_id)

PermissionAssociation.__table_args__ = (fk,uq) + table_args

MAX_KEY_LEN = 255
MAX_SECRET_LEN = 255
KEY_LEN = 32
SECRET_LEN = 32

class OAuthConsumer(Base):
    __tablename__ = 'auth_oauth_consumer'
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    key = Column(String(MAX_KEY_LEN), unique=True)
    secret = Column(String(MAX_SECRET_LEN))

    user = relationship(User, lazy=True, uselist=False)

    def __init__(self, **kwargs):
        super(OAuthConsumer, self).__init__(**kwargs)
        if not self.key:
            self.key = random_string(size=KEY_LEN)
        if not self.secret:
            self.secret = random_string(size=SECRET_LEN)

    @classmethod
    def create(cls, user_id, **kwargs):
        kwargs['id'] = user_id
        return cls(**kwargs)

    def as_consumer(self):
        '''Creates an oauth.OAuthConsumer object from the DB data.
        :rtype: oauth.OAuthConsumer
        '''
        return oauth.OAuthConsumer(self.key, self.secret)

class OAuthNonce(Base):
    __tablename__ = 'auth_oauth_nonce'
    id = Column(Integer, primary_key=True)
    token_key = Column(String(32))
    consumer_key = Column(String(MAX_KEY_LEN), ForeignKey(OAuthConsumer.key))
    key = Column(String(255), nullable=False, unique=True)

