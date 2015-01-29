from __future__ import absolute_import
from collections import defaultdict
from importlib import import_module
import sys
import warnings

from django.conf import settings
from django.forms import ValidationError
from django.utils.deprecation import RemovedInDjango19Warning
from sqlalchemy import event, inspect
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.ext.declarative.base import (_as_declarative, _add_attribute)
from sqlalchemy.ext.declarative.clsregistry import add_class
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.orm import mapper, object_session, class_mapper
from sqlalchemy.orm.attributes import instance_dict, instance_state
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import has_identity, identity_key
from sqlalchemy.schema import ForeignKeyConstraint

from baph.apps import apps
from baph.apps.config import MODELS_MODULE_NAME
from baph.db import ORM
from baph.db.models import signals
from baph.db.models.mixins import CacheMixin, ModelPermissionMixin, GlobalMixin
from baph.db.models.options import Options
from baph.db.models.utils import class_resolver, key_to_value
from baph.utils.importing import safe_import, remove_class


@compiles(ForeignKeyConstraint)
def set_default_schema(constraint, compiler, **kw):
    #print constraint, (compiler,), kw
    """ This overrides the formatting function used to render remote tables
        in foreign key declarations, because innodb (at least, perhaps others)
        requires explicit schemas when declaring a FK which crosses schemas """
    remote_table = list(constraint._elements.values())[0].column.table
   
    if remote_table.schema is None:
        default_schema = remote_table.bind.url.database
        #print (constraint.columns[0],)
        print (constraint.table,)
        if constraint.table is not None:
            constraint_schema = constraint.table.schema
        else:
            constraint_schema = constraint.columns[0].table.schema
        if constraint_schema not in (default_schema, None):
            """ if the constraint schema is not the default, we need to 
                add a schema before formatting the table """
            remote_table.schema = default_schema
            value = compiler.visit_foreign_key_constraint(constraint, **kw)
            remote_table.schema = None
            return value
    return compiler.visit_foreign_key_constraint(constraint, **kw)

def constructor(self, ignore_unknown_kwargs=False, **kwargs):
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
        if not hasattr(cls, k) and not ignore_unknown_kwargs:
            raise TypeError('%r is an invalid keyword argument for %s' %
                (k, cls.__name__))
        setattr(self, k, kwargs[k])

@event.listens_for(mapper, 'mapper_configured')
def set_polymorphic_base_mapper(mapper_, class_):
    if mapper_.polymorphic_on is not None:
        polymorphic_map = defaultdict(lambda: mapper_)
        polymorphic_map.update(mapper_.polymorphic_map)
        mapper_.polymorphic_map = polymorphic_map

class Model(CacheMixin, ModelPermissionMixin, GlobalMixin):

    def __init__(self, *args, **kwargs):
        signals.pre_init.send(sender=self.__class__, args=args, kwargs=kwargs)
        super(Model, self).__init__(self, *args, **kwargs)
        signals.post_init.send(sender=self.__class__, instance=self)

    @classmethod
    def list_actions(cls, user, ns):
        for action in cls._meta.list_actions:
            label = action.capitalize()
            view = '%s:%s' % (ns, action)
            if action.find('.') > -1:
                obj_name, action = action.split('.', 1)
            else:
                obj_name = cls._meta.object_name
            if user.has_perm(obj_name, action):
                yield (label, view)

    def actions(self, user, ns):
        cls, args = identity_key(instance=self)
        for action in self._meta.detail_actions:
            label = action.capitalize()
            view = '%s:%s' % (ns, action)
            if action.find('.') > -1:
                obj_name, action = action.split('.', 1)
            else:
                obj_name = self._meta.object_name
            if user.has_obj_perm(obj_name, action, self):
                yield (label, view, args)

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

    @property
    def pk_kwargs(self):
        cls, values = identity_key(instance=self)
        mapper = inspect(cls)
        keys = [mapper.get_property_by_column(col).key \
                    for col in mapper.primary_key]
        values = mapper.primary_key_from_instance(self)
        return dict(zip(keys, values))

    def update(self, data):
        for key, value in data.iteritems():
            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)       

    def delete(self):
        if has_identity(self):
            session = object_session(self)
            session.delete(self)
            session.commit()

    @property
    def js_data_string(self):
        parts = ['data-%s="%s"' % (k,v) for k,v in self.pk_kwargs.items()]
        return ' '.join(parts)

    def to_dict(self):
        '''Creates a dictionary out of the column properties of the object.
        This is needed because it's sometimes not possible to just use
        :data:`__dict__`.

        :rtype: :class:`dict`
        '''
        __dict__ = dict([(key, val) for key, val in self.__dict__.iteritems()
                         if not key.startswith('_sa_')])
        if len(__dict__) == 0:
            for attr in inspect(type(self)).all_orm_descriptors:
                if not hasattr(attr, 'property'):
                    continue
                if not isinstance(attr.property, ColumnProperty):
                    continue
                __dict__[attr.key] = getattr(self, attr.key)
        return __dict__

    @property
    def is_deleted(self):
        return False

    def save(self, commit=False):
        from baph.db.orm import ORM
        orm = ORM.get()
        session = orm.sessionmaker()

        if commit:
            if not self in session:
                session.add(self)
            session.commit()

        

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


    def __new__(cls, name, bases, attrs):
        print '%s.__new__(%s)' % (name, cls)

        req_sub = attrs.pop('__requires_subclass__', False)

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

        # Look for an application configuration to attach the model to.
        app_config = apps.get_containing_app_config(module)

        if getattr(meta, 'app_label', None) is None:

            if app_config is None:
                # If the model is imported before the configuration for its
                # application is created (#21719), or isn't in an installed
                # application (#21680), use the legacy logic to figure out the
                # app_label by looking one level up from the package or module
                # named 'models'. If no such package or module exists, fall
                # back to looking one level up from the module this model is
                # defined in.

                # For 'django.contrib.sites.models', this would be 'sites'.
                # For 'geo.models.places' this would be 'geo'.

                msg = (
                    "Model class %s.%s doesn't declare an explicit app_label "
                    "and either isn't in an application in INSTALLED_APPS or "
                    "else was imported before its application was loaded. " %
                    (module, name))
                if False: #abstract: #TODO: test SA __abstract__ here and see if it breaks
                    msg += "Its app_label will be set to None in Django 1.9."
                else:
                    msg += "This will no longer be supported in Django 1.9."
                warnings.warn(msg, RemovedInDjango19Warning, stacklevel=2)

                model_module = sys.modules[new_class.__module__]
                package_components = model_module.__name__.split('.')
                package_components.reverse()  # find the last occurrence of 'models'
                try:
                    app_label_index = package_components.index(MODELS_MODULE_NAME) + 1
                except ValueError:
                    app_label_index = 1
                #kwargs = {"app_label": package_components[app_label_index]}
                kwargs = {"app_label": '.'.join(reversed(package_components[app_label_index:]))}

            else:
                kwargs = {"app_label": app_config.label}

        else:
            kwargs = {}

        new_class.add_to_class('_meta', Options(meta, **kwargs))
        if base_meta:
            # Non-abstract child classes inherit some attributes from their
            # non-abstract parent (unless an ABC comes before it in the
            # method resolution order).
            for k,v in vars(base_meta).items():
                if not getattr(new_class._meta, k, None):
                    setattr(new_class._meta, k, v)

        if new_class._meta.swappable:
            if not new_class._meta.swapped:
                # class is swappable, but hasn't been swapped out, so we create
                # an alias to the base class, rather than trying to create a new
                # class under a second name
                base_cls  = bases[0]
                base_cls.add_to_class('_meta', new_class._meta)
                new_class._meta.apps.register_model(base_cls._meta.app_label, base_cls)
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
            #print '\t', obj_name
            new_class.add_to_class(obj_name, obj)
        
        if attrs.get('__abstract__', None):
            return new_class

        new_class._prepare()
        new_class._meta.apps.register_model(new_class._meta.app_label, new_class)
        return new_class

    def __setattr__(cls, key, value):
        _add_attribute(cls, key, value)

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def _prepare(cls):
        """
        Creates some methods once self._meta has been populated.
        """
        opts = cls._meta
        #opts._prepare(cls)

        # Give the class a docstring -- its definition.
        '''
        if cls.__doc__ is None:
            cls.__doc__ = "%s(%s)" % (cls.__name__, ", ".join(f.attname for f in opts.fields))

        if hasattr(cls, 'get_absolute_url'):
            cls.get_absolute_url = update_wrapper(curry(get_absolute_url, opts, cls.get_absolute_url),
                                                  cls.get_absolute_url)
        '''
        signals.class_prepared.send(sender=cls)

    def get_prop_from_proxy(cls, proxy):
        if proxy.scalar:
            # column
            prop = proxy.remote_attr.property
        elif proxy.remote_attr.extension_type == ASSOCIATION_PROXY:
            prop = cls.get_prop_from_proxy(proxy.remote_attr)
        elif isinstance(proxy.remote_attr.property, RelationshipProperty):
            prop = proxy.remote_attr.property
        else:
            prop = proxy.remote_attr.property
        return prop

    @property
    def all_properties(cls):
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

    @property
    def resource_name(cls):
        try:
            if cls.__mapper__.polymorphic_on is not None:
                return cls.__mapper__.primary_base_mapper.class_.resource_name
        except:
            pass
        return cls._meta.object_name

    def get_base_class(cls):
        """Returns the base class if polymorphic, else the class itself"""
        try:
            if cls.__mapper__.polymorphic_on is not None:
                return cls.__mapper__.primary_base_mapper.class_
        except:
            pass
        return cls


def get_declarative_base(**kwargs):
    return declarative_base(cls=Model, 
        metaclass=ModelBase,
        constructor=constructor,
        **kwargs)

if getattr(settings, 'CACHE_ENABLED', False):
    @event.listens_for(mapper, 'after_insert')
    @event.listens_for(mapper, 'after_update')
    @event.listens_for(mapper, 'after_delete')
    def kill_cache(mapper, connection, target):
        target.kill_cache()

@event.listens_for(Session, 'before_flush')
def check_global_status(session, flush_context, instances):
    """
    If global_parents is defined, we check the parents to see if any of them
    are global. If a global parent is found, we set the child to global as well
    """
    for target in session:
        if target._meta.global_parents:
            if target.is_globalized():
                continue
            for parent_rel in target._meta.global_parents:
                parent = key_to_value(target, parent_rel, raw=True)
                if parent and parent.is_globalized():
                    target.globalize(commit=False)
                    break

