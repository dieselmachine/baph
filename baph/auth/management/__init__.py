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
    perms = []
    classes = opts.permission_classes
    actions = opts.permission_actions
    handler = opts.permission_handler
    if handler or not classes or not actions:
        return perms
    fks = opts.model.get_fks()
    for klass in classes:
        for action in actions:
            for limiter, key, value, rel_key, base_class in fks:
                if (action,limiter) == ('add', 'single'):
                    # this permission makes no sense, skip it
                    continue
                if key and key.find('.') > -1:
                    frags = key.split('.')[:-2]
                    if frags:
                        limiter += ' ' + ' '.join(reversed(frags))
                    frags.append(rel_key)
                    key = '.'.join(frags)
                perm_name = 'Can %s %s %s' % (action, limiter, klass)
                perms.append(auth_app.Permission(
                    name=perm_name,
                    codename=perm_name.lower().replace(' ','_'),
                    resource=klass,
                    action=action,
                    key=key,
                    value=value,
                    base_class=base_class
                    ))
    return perms

def create_permissions(app, created_models, verbosity, db=DEFAULT_DB_ALIAS,
                       **kwargs):
    #print 'create perm for app:', app
    app_models = []
    for k, v in vars(app).items():
        if k not in Base._decl_class_registry:
            continue
        if v not in Base._decl_class_registry.values():
            continue
        if hasattr(app, '__package__') and app.__package__ + '.models' != v.__module__:
            continue
        app_models.append( (k,v) )
    if not app_models:
        return

    searched_perms = list()
    searched_codenames = set()
    for k, klass in sorted(app_models, key=lambda x: x[0]):
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
