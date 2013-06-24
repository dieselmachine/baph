from __future__ import absolute_import
from collections import defaultdict
from importlib import import_module
import sys

from django.conf import settings
from django.forms import ValidationError
from sqlalchemy import event, inspect
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.ext.declarative.base import (_as_declarative, _add_attribute,
    _MapperConfig)
from sqlalchemy.ext.declarative.clsregistry import add_class
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.orm import mapper, configure_mappers
from sqlalchemy.orm.attributes import instance_dict, instance_state
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty

from baph.db.models.loading import get_model, register_models
from baph.db.models.mixins import CacheMixin, ModelPermissionMixin
from baph.db.models.options import Options
from baph.db.models import signals
from baph.utils.importing import safe_import, remove_class


def constructor(self, **kwargs):
    cls = type(self)

    # auto-populate default values on init
    for attr in cls.__mapper__.all_orm_descriptors:
        if not hasattr(attr, 'property'):
            continue
        if not isinstance(attr.property, ColumnProperty):
            continue
        if attr.key in kwargs:
            continue
        if len(attr.property.columns) != 1:
            continue
        col = attr.property.columns[0]
        if not hasattr(col, 'default'):
            continue
        if col.default is None:
            continue
        default = col.default.arg
        if callable(default):
            setattr(self, attr.key, default({}))
        else:
            setattr(self, attr.key, default)

    # now load in the kwargs values
    for k in kwargs:
        if not hasattr(cls, k):
            raise TypeError('%r is an invalid keyword argument for %s' %
                (k, cls.__name__))
        setattr(self, k, kwargs[k])

@event.listens_for(mapper, 'mapper_configured')
def set_polymorphic_base_mapper(mapper_, class_):
    if mapper_.polymorphic_on is not None:
        polymorphic_map = defaultdict(lambda: mapper_)
        polymorphic_map.update(mapper_.polymorphic_map)
        mapper_.polymorphic_map = polymorphic_map

class Model(CacheMixin, ModelPermissionMixin):

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def get_form_class(cls, *args, **kwargs):
        if not cls._meta.form_class:
            return None
        cls_path = cls._meta.form_class
        cls_mod, cls_name = cls_path.rsplit('.', 1)
        module = import_module(cls_mod)
        return getattr(module, cls_name)

    def update(self, data):
        for key, value in data.iteritems():
            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)       

    @property
    def is_deleted(self):
        return False

class ModelBase(type):

    def __init__(cls, name, bases, attrs):
        #print '%s.__init__(%s)' % (name, cls)
        found = False
        registry = cls._decl_class_registry
        if name in registry:
            found = True
        elif cls in registry.values():
            found = True
            add_class(name, cls)

        if '_decl_class_registry' not in cls.__dict__:
            if not found:
                _as_declarative(cls, name, cls.__dict__)

        type.__init__(cls, name, bases, attrs)

    def __setattr__(cls, key, value):
        _add_attribute(cls, key, value)

    def __new__(cls, name, bases, attrs):
        #print '%s.__new__(%s)' % (name, cls)
        super_new = super(ModelBase, cls).__new__

        parents = [b for b in bases if isinstance(b, ModelBase) and
            not (b.__name__ == 'Base' and b.__mro__ == (b, object))]
        if not parents:
            return super_new(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})

        # check the class registry to see if we created this already
        if name in new_class._decl_class_registry:
            return new_class._decl_class_registry[name]

        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)

        if getattr(meta, 'app_label', None) is None:
            # Figure out the app_label by looking one level up.
            # For 'django.contrib.sites.models', this would be 'sites'.
            model_module = sys.modules[new_class.__module__]
            kwargs = {"app_label": model_module.__name__.rsplit('.',1)[0]}
        else:
            kwargs = {}

        new_class.add_to_class('_meta', Options(meta, **kwargs))
        if base_meta:
            for k,v in vars(base_meta).items():
                if not getattr(new_class._meta, k, None):
                    setattr(new_class._meta, k, v)

        if new_class._meta.swappable:
            if not new_class._meta.swapped:
                # class is swappable, not hasn't been swapped out, so we create
                # an alias to the base class, rather than trying to create a new
                # class under a second name
                base_cls  = bases[0]
                base_cls.add_to_class('_meta', new_class._meta)
                return base_cls

            # class has been swapped out
            model = safe_import(new_class._meta.swapped, [new_class.__module__])

            for b in bases:
                if not getattr(b, '__mapper__', None):
                    continue
                if not getattr(b, '_sa_class_manager', None):
                    continue
                subs = [c for c in b.__subclasses__() if c.__name__ != name]
                if any(c.__name__ != name for c in b.__subclasses__()):
                    # this base class has a subclass inheriting from it, so we
                    # should leave this class alone, we'll need it
                    continue
                else:
                    # this base class is used by no subclasses, so it can be
                    # removed from appcache/cls registry/mod registry
                    remove_class(b, name)
            return model

        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)
        
        if attrs.get('__abstract__', None):
            return new_class

        signals.class_prepared.send(sender=new_class)
        register_models(new_class._meta.app_label, new_class)
        return get_model(new_class._meta.app_label, name,
                         seed_cache=False, only_installed=False)


    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def get_prop_from_proxy(cls, proxy):
        if proxy.remote_attr.extension_type == ASSOCIATION_PROXY:
            # proxy
            prop = cls.get_prop_from_proxy(proxy.remote_attr)
        elif isinstance(proxy.remote_attr.property, RelationshipProperty):
            # relationship
            prop = proxy.remote_attr.property
        else:
            # column
            prop = proxy.remote_attr.property
        return prop

    @property
    def all_properties(cls):
        if not cls.__mapper__.configured:
            configure_mappers()
        for key, attr in inspect(cls).all_orm_descriptors.items():
            if attr.is_mapper:
                continue
            elif attr.extension_type == HYBRID_METHOD:
                # not a property
                continue
            elif attr.extension_type == HYBRID_PROPERTY:
                prop = attr
            elif attr.extension_type == ASSOCIATION_PROXY:
                proxy = getattr(cls, key)
                prop = cls.get_prop_from_proxy(proxy)
            elif isinstance(attr.property, ColumnProperty):
                prop = attr.property
            elif isinstance(attr.property, RelationshipProperty):
                prop = attr.property
            yield (key, prop)


Base = declarative_base(cls=Model, 
    metaclass=ModelBase,
    constructor=constructor)


if getattr(settings, 'CACHE_ENABLED', False):
    @event.listens_for(mapper, 'after_insert')
    @event.listens_for(mapper, 'after_update')
    @event.listens_for(mapper, 'after_delete')
    def kill_cache(mapper, connection, target):
        target.kill_cache()
