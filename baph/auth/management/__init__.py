from __future__ import unicode_literals
import getpass
import locale
import unicodedata

from django.core import exceptions
from django.core.management.base import CommandError
from django.db import DEFAULT_DB_ALIAS, router
from django.utils.encoding import DEFAULT_LOCALE_ENCODING
try:
    from django.utils.text import slugify
except:
    from django.template.defaultfilters import slugify
from sqlalchemy.ext.declarative import has_inherited_table

from baph.auth import models as auth_app #, get_user_model
from baph.db.models import get_models
from baph.db.orm import Base, ORM
#from baph.db import Session
#from baph.db.models import signals, get_models


orm = ORM.get()

def _get_permission_codename(action, opts, label=None):
    label = label if label else opts.model_name
    codename = '%s_%s' % (action, label)
    return slugify(codename.replace(' ','_'))
    
def _get_all_permissions(opts):
    """
    Returns (action, scope, codename, name) for all permissions in the given opts.
    """
    builtin = _get_builtin_permissions(opts)
    custom = _get_custom_permissions(opts)
    _check_permission_clashing(custom, builtin)
    return builtin + custom
    
def _get_builtin_permissions(opts):
    """
    Returns (action, scope, codename, name) for all autogenerated permissions.
    """
    perms = []
    for action in ('view', 'add', 'edit', 'delete'):
        perms.append(auth_app.Permission(
            name='Can %s %s' % (action, opts.verbose_name),
            codename=_get_permission_codename(action, opts),
            resource=opts.object_name,
            action=action,
            ))
    return perms
    
def _get_custom_permissions(opts):
    scopes = opts.permission_scopes
    perms = []
    for action, scope_ids in opts.permissions.items():
        if not isinstance(scope_ids, (list, tuple)):
            raise Exception('%s.Meta.permissions["%s"] is not iterable'
                % (resource, action))

        for scope_id in scope_ids:
            if scope_id and scope_id not in scopes:
                # undefined scope
                raise Exception('scope_id "%s" was not found in '
                    'scope_permissions (found %s)' % (scope_id,
                        ', '.join(scopes.keys())))

            kwargs = {
                'resource': opts.object_name,
                'action': action,
                'key': None,
                'value': None,
                }

            if scope_id is None:
                # boolean permission
                label = opts.verbose_name
                kwargs.update({
                    'name': 'Can %s %s' % (action, label),
                    'codename': _get_permission_codename(action, opts),
                    })
            else:
                # filter permission
                scope = scopes[scope_id]
                if len(scope) == 2:
                    label = '%s %s' % (scope_id, opts.model_name)
                elif len(scope) >= 3:
                    label = scope[2]
                else:
                    raise Exception('scope %s (%s) must contain at least 2 '
                        'items')

                if len(scope) >= 4:
                    kwargs['resource'] = scope[3]

                kwargs.update({
                    'name': 'Can %s %s' % (action, label),
                    'codename': _get_permission_codename(action, opts, label),
                    'key': scope[0],
                    'value': scope[1],
                    })
            perms.append(auth_app.Permission(**kwargs))

    return perms
    
def _check_permission_clashing(custom, builtin):
    """
    Check that permissions for a model do not clash. Raises CommandError if
    there are duplicate permissions.
    """
    pool = set()
    builtin_codenames = set(p.codename for p in builtin)
    for perm in custom:
        if perm.codename in pool:
            raise CommandError(
                "The permission codename '%s' is duplicated"
                % perm.codename)
        elif perm.codename in builtin_codenames:
            raise CommandError(
                "The permission codename '%s' clashes with a builtin permission "
                % (perm.codename,)) # ctype.app_label, ctype.model_class().__name__))
        pool.add(perm.codename)

def create_permissions(app, created_models, verbosity, db=DEFAULT_DB_ALIAS,
                       **kwargs):
    app_models = []
    for k, v in vars(app).items():
        if k in Base._decl_class_registry and \
           v in Base._decl_class_registry.values():
            app_models.append(v)
    if not app_models:
        return

    searched_perms = list()
    searched_codenames = set()
    for klass in app_models:
        if klass.__mapper__.polymorphic_on is not None:
            if has_inherited_table(klass):
                # ignore polymorphic subclasses
                continue
        elif klass.__subclasses__():
            # ignore base if subclass is present
            continue
        for perm in _get_all_permissions(klass._meta):
            if perm.codename in searched_codenames:
                continue
            searched_perms.append(perm)
            searched_codenames.add(perm.codename)

    session = orm.sessionmaker()    
    all_perms = session.query(auth_app.Permission).all()
    all_codenames = set(p.codename for p in all_perms)

    perms = [
        perm for perm in searched_perms
        if perm.codename not in all_codenames
        ]
    session.add_all(perms)
    session.commit()

    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '%s:%s'" % (perm.resource, perm.codename))
