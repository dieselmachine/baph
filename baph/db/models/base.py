from __future__ import absolute_import
from collections import defaultdict
from importlib import import_module
import sys
import warnings

from django.conf import settings
from django.forms import ValidationError
from django.utils.deprecation import RemovedInDjango19Warning
from sqlalchemy import event, inspect
from sqlalchemy.ext.associationproxy import *
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.ext.declarative.base import _as_declarative, _add_attribute
from sqlalchemy.ext.declarative.clsregistry import add_class
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.orm import mapper, object_session, class_mapper, interfaces
from sqlalchemy.orm.attributes import instance_dict, instance_state
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import has_identity, identity_key
from sqlalchemy.schema import ForeignKeyConstraint

from baph.apps import apps
from baph.apps.config import MODELS_MODULE_NAME
from baph.db.models import signals
from baph.db.models.manager import ensure_default_manager
from baph.db.models.mixins import CacheMixin, ModelPermissionMixin, GlobalMixin
from baph.db.models.options import Options
from baph.db.models.utils import class_resolver, key_to_value
from baph.utils.importing import safe_import, remove_class


@compiles(ForeignKeyConstraint)
def set_default_schema(constraint, compiler, **kw):
    """ This overrides the formatting function used to render remote tables
        in foreign key declarations, because innodb (at least, perhaps others)
        requires explicit schemas when declaring a FK which crosses schemas """
    remote_table = list(constraint._elements.values())[0].column.table
   
    if remote_table.schema is None:
        default_schema = remote_table.bind.url.database
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

@event.listens_for(mapper, 'mapper_configured')
def set_polymorphic_base_mapper(mapper_, class_):
    if mapper_.polymorphic_on is not None:
        polymorphic_map = defaultdict(lambda: mapper_)
        polymorphic_map.update(mapper_.polymorphic_map)
        mapper_.polymorphic_map = polymorphic_map

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


class BaseModel(CacheMixin, ModelPermissionMixin, GlobalMixin):

    def __init__(self, *args, **kwargs):
        signals.pre_init.send(sender=self.__class__, args=args, kwargs=kwargs)
        super(BaseModel, self).__init__(self, *args, **kwargs)
        signals.post_init.send(sender=self.__class__, instance=self)

    @classmethod
    def get_fields(cls, owner_id=None):
        # calling __get__ on proxies sets the owning_class attr.
        # without this, attempting to read most other attrs will fail
        # we also set the key, because it doesn't exist on the proxy itself
        mapper = inspect(cls)
        proxies = []
        for key, attr in mapper.all_orm_descriptors.items():
            if attr.extension_type == ASSOCIATION_PROXY:
                attr = getattr(cls, key)
                attr.key = key
                proxies.append(attr)
        '''
        print 'get_fields:', cls
        for prop in mapper.column_attrs:
            print '  [col]', prop
        for prop in mapper.relationships:
            print '  [rel]', prop
        for prop in proxies:
            print '  [prx]', prop
        '''
        return mapper.column_attrs + mapper.relationships + proxies

    @classmethod
    def get_custom_fields(cls, owner_id):
        from baph.contrib.custom_fields.models import CustomField
        from baph.db.orm import ORM
        orm = ORM.get()
        if not cls._meta.extension_field:
            return
            raise Exception('extension_field must be defined')
        session = orm.sessionmaker()
        custom_fields = session.query(CustomField) \
            .filter_by(owner_id=owner_id) \
            .filter_by(model=cls._meta.object_name) \
            .all()
        for field in custom_fields:
            yield field.as_modelfield()

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

    def save(self, commit=False, force_insert=False, force_update=False,
             using=None, update_fields=None):
        """
        Saves the current instance. Override this in a subclass if you want to
        control the saving process.
        The 'force_insert' and 'force_update' parameters can be used to insist
        that the "save" must be an SQL insert or update (or equivalent for
        non-SQL backends), respectively. Normally, they should not be set.
        """
        #using = using or router.db_for_write(self.__class__, instance=self)

        if update_fields is not None:
            # If update_fields is empty, skip the save. We do also check for
            # no-op saves later on for inheritance cases. This bailout is
            # still needed for skipping signal sending.
            if len(update_fields) == 0:
                return

        update_fields = frozenset(update_fields)
        field_names = set()

        for field in self._meta.fields:
            if not field.primary_key:
                field_names.add(field.name)

                if field.name != field.attname:
                    field_names.add(field.attname)

        non_model_fields = update_fields.difference(field_names)

        if non_model_fields:
            raise ValueError("The following fields do not exist in this "
                             "model or are m2m fields: %s"
                             % ', '.join(non_model_fields))

        self.save_base(using=using, force_insert=force_insert,
                       force_update=force_update, update_fields=update_fields)
    save.alters_data = True

    def save_base(self, commit=False, raw=False, force_insert=False,
                  force_update=False, using=None, update_fields=None):
        """
        Handles the parts of saving which should be done only once per save,
        yet need to be done in raw saves, too. This includes some sanity
        checks and signal sending.
        The 'raw' argument is telling save_base not to save any parent
        models and not to do any changes to the values before save. This
        is used by fixture loading.
        """
        using = using or router.db_for_write(self.__class__, instance=self)
        assert not (force_insert and (force_update or update_fields))
        assert update_fields is None or len(update_fields) > 0
        cls = origin = self.__class__
        # Skip proxies, but keep the origin as the proxy model.
        #if cls._meta.proxy:
        #    cls = cls._meta.concrete_model
        meta = cls._meta
        #if not meta.auto_created:
        #    signals.pre_save.send(sender=origin, instance=self, raw=raw, using=using,
        #                          update_fields=update_fields)
        #with transaction.atomic(using=using, savepoint=False):
        #    if not raw:
        #        self._save_parents(cls, using, update_fields)
        #    updated = self._save_table(raw, cls, force_insert, force_update, using, update_fields)
        # Store the database on which the object was saved
        #self._state.db = using
        # Once saved, this is no longer a to-be-added instance.
        #self._state.adding = False

        from baph.db.orm import ORM
        orm = ORM.get()
        session = orm.sessionmaker()

        if commit:
            if not self in session:
                session.add(self)
            session.commit()

        # Signal that the save is complete
        if not meta.auto_created:
            signals.post_save.send(sender=origin, instance=self, 
                                   created=(not updated),
                                   update_fields=update_fields,
                                   raw=raw, using=using)

    save_base.alters_data = True


    def _get_next_or_previous_by_FIELD(self, field, is_next, **kwargs):
        print 'get next or previous:', (self, field, is_next, kwargs)
        assert False

    def clean(self):
        """
        Hook for doing any extra model-wide validation after clean() has been
        called on every field by self.clean_fields. Any ValidationError raised
        by this method will not be associated with a particular field; it will
        have a special-case association with the field defined by NON_FIELD_ERRORS.
        """
        pass

    def full_clean(self, exclude=None, validate_unique=True):
        """
        Calls clean_fields, clean, and validate_unique, on the model,
        and raises a ``ValidationError`` for any errors that occurred.
        """
        errors = {}
        if exclude is None:
            exclude = []
        else:
            exclude = list(exclude)

        try:
            self.clean_fields(exclude=exclude)
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        # Form.clean() is run even if other validation fails, so do the
        # same with Model.clean() for consistency.
        try:
            self.clean()
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        # Run unique checks, but only for fields that passed validation.
        if validate_unique:
            for name in errors.keys():
                if name != NON_FIELD_ERRORS and name not in exclude:
                    exclude.append(name)
            try:
                self.validate_unique(exclude=exclude)
            except ValidationError as e:
                errors = e.update_error_dict(errors)

        if errors:
            raise ValidationError(errors)

    def clean_fields(self, exclude=None):
        """
        Cleans all fields and raises a ValidationError containing a dict
        of all validation errors if any occur.
        """
        if exclude is None:
            exclude = []

        errors = {}
        #print 'clean fields:', (self,)
        for f in self._meta.fields:
            if f.name in exclude:
                #print '    ignoring excluded field "%s"' % f.name
                continue
            # Skip validation for empty fields with blank=True. The developer
            # is responsible for making sure they have a valid value.
            #print '    cleaning field "%s"' % f.name
            raw_value = getattr(self, f.attname)
            if f.blank and raw_value in f.empty_values:
                continue
            try:
                setattr(self, f.attname, f.clean(raw_value, self))
            except ValidationError as e:
                errors[f.name] = e.error_list

        if errors:
            raise ValidationError(errors)

class ModelBase(type):
    """
    Metaclass for all models.
    """
    def __init__(cls, name, bases, attrs):
        #print '%s.__init__ start' % name
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
        #print '%s.__init__ end' % name
    
    def __new__(cls, name, bases, attrs):
        #print '%s.__new__' % name
        super_new = super(ModelBase, cls).__new__
        
        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        # If this class was already created, return the existing version from
        # the SQLA class registry (This will happen if safe_import performs a
        # partial import while importing a swapped class, then later returns to
        # the file to import the remainder)
        registry = parents[0]._decl_class_registry
        if name in registry:
            return registry[name]

        if attrs.get('__abstract__', False):
            return super_new(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        attr_meta = attrs.pop('Meta', None)

        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)

        app_label = None

        # Look for an application configuration to attach the model to.
        app_config = apps.get_containing_app_config(module)

        if getattr(meta, 'app_label', None) is None:
            if app_config is None:
                if not abstract:
                    raise RuntimeError(
                        "Model class %s.%s doesn't declare an explicit "
                        "app_label and either isn't in an application in "
                        "INSTALLED_APPS or else was imported before its "
                        "application was loaded. " % (module, name))

            else:
                app_label = app_config.label

        new_class.add_to_class('_meta', Options(meta, app_label=app_label))
        if base_meta:
            # Non-abstract child classes inherit some attributes from their
            # non-abstract parent (unless an ABC comes before it in the
            # method resolution order).
            for k,v in vars(base_meta).items():
                if not getattr(new_class._meta, k, None):
                    setattr(new_class._meta, k, v)

        if new_class._meta.swappable:
            #print '  class is swappable'
            if not new_class._meta.swapped:
                # class is swappable, but hasn't been swapped out, so we create
                # an alias to the base class, rather than trying to create a new
                # class under a second name
                base_cls = bases[0]
                base_cls.add_to_class('_meta', new_class._meta)
                new_class._meta.apps.register_model(base_cls._meta.app_label, base_cls)
                return base_cls
            #print '  class was swapped'
            # class has been swapped out
            model = safe_import(new_class._meta.swapped, [new_class.__module__])

            for b in parents:
                # remove any parents that aren't in use
                if any(s.__module__ != module or s.__name__ != name
                        for s in b.__subclasses__()):
                    continue
                else:
                    #print '  removing unused class: ', b
                    remove_class(b, name)
            #print '  returning swapped model', model
            return model

        # Add all attributes to the class.
        #print new_class
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)
        
        new_class._prepare()
        new_class._meta.apps.register_model(new_class._meta.app_label, new_class)
        return new_class
    
    def __setattr__(cls, key, value):
        try:
            junk = value.__module__.startswith('django.db.models.fields.related')
        except:
            junk = False
        if not junk:
            _add_attribute(cls, key, value)

    def add_to_class(cls, name, value):
        # We should call the contribute_to_class method only if it's bound
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def _prepare(cls):
        """
        Creates some methods once self._meta has been populated.
        """
        #print cls, '_prepare'
        opts = cls._meta
        opts._prepare(cls)

        # Give the class a docstring -- its definition.
        #if cls.__doc__ is None:
        #    cls.__doc__ = "%s(%s)" % (cls.__name__, ", ".join(f.name for f in opts.fields))

        #get_absolute_url_override = settings.ABSOLUTE_URL_OVERRIDES.get(opts.label_lower)
        #if get_absolute_url_override:
        #    setattr(cls, 'get_absolute_url', get_absolute_url_override)

        ensure_default_manager(cls)
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
    return declarative_base(cls=BaseModel, 
        metaclass=ModelBase,
        constructor=constructor,
        **kwargs)

Base = Model = get_declarative_base()

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

