import inspect as inspect_
from types import FunctionType

from baph.db import types
from django.db.models import fields as modelfields
from jsonfield import JSONField
from sqlalchemy import *
from sqlalchemy import inspect
from sqlalchemy import interfaces
from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.ext.associationproxy import *
from sqlalchemy.ext.declarative import declarative_base, clsregistry
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm.base import *
from sqlalchemy.orm.collections import MappedCollection
from sqlalchemy.ext.declarative.clsregistry import _class_resolver
from sqlalchemy.ext.orderinglist import OrderingList
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.util import duck_type_collection


MODELFIELD_MAP = {
    'auto':                     modelfields.AutoField,
    Boolean:                    modelfields.BooleanField,
    String:                     modelfields.CharField,
    Unicode:                    modelfields.CharField,
    'csi':                      modelfields.CommaSeparatedIntegerField,
    Date:                       modelfields.DateField,
    DateTime:                   modelfields.DateTimeField,
    Float:                      modelfields.DecimalField,
    types.Duration:             modelfields.DurationField,
    types.EmailAddress:         modelfields.EmailField,
    'filepath':                 modelfields.FilePathField,
    'float':                    modelfields.FloatField,
    Integer:                    modelfields.IntegerField,
    'bigint':                   modelfields.BigIntegerField,
    'ip':                       modelfields.IPAddressField,
    'genip':                    modelfields.GenericIPAddressField,
    'nullbool':                 modelfields.NullBooleanField,
    'posint':                   modelfields.PositiveIntegerField,
    'psi':                      modelfields.PositiveSmallIntegerField,
    'slug':                     modelfields.SlugField,
    'smallint':                 modelfields.SmallIntegerField,
    Text:                       modelfields.TextField,
    UnicodeText:                modelfields.TextField,
    Time:                       modelfields.TimeField,
    types.URL:                  modelfields.URLField,
    'binary':                   modelfields.BinaryField,
    #'uuid':                    modelfields.UUIDField,
    'file':                     modelfields.files.FileField,
    'image':                    modelfields.files.ImageField,
    JSON:                       JSONField,
    types.Dict:                 JSONField,
    types.PhoneNumber:          modelfields.CharField,
    }

def has_inherited_table(cls):
    # TODO: a fix in sqla 0.9 should make this unnecessary, check it
    """
    Takes a class, return True if any of the classes it inherits from has a
    mapped table, otherwise return False.
    """
    for class_ in cls.__mro__:
        if cls == class_:
            continue
        if getattr(class_, '__table__', None) is not None:
            return True
    return False

def class_resolver(cls):
    """
    Takes a class, string, or lazy resolver and returns the
    appropriate SQLA class
    """
    from baph.db.models.base import Model as Base
    if isinstance(cls, basestring):
        # string reference
        cls = Base._decl_class_registry[cls]
    if isinstance(cls, FunctionType):
        # lazy-loaded Model
        cls = cls()
    elif isinstance(cls, _class_resolver):
        # lazy-loaded Model
        cls = cls()
    elif hasattr(cls, 'is_mapper') and cls.is_mapper:
        # we found a mapper, grab the class from it
        cls = cls.class_
    if issubclass(cls, Base):
        # sqla class
        return cls
    raise Exception('could not resolve class: %s' % cls)

def collection_resolver(collection):
    if isinstance(collection, FunctionType):
        collection = type(collection())
    if collection:
        collection = duck_type_collection(collection)
    return collection

def column_to_attr(cls, col):
    """
    Takes a class and a column and returns the attribute which 
    references the column
    """
    if hasattr(cls, col.name):
        # the column name is the same as the attr name
        return getattr(cls, col.name)
    for attr_ in inspect(cls).all_orm_descriptors:
        # iterate through descriptors to find one that contains the column
        try:
            assert attr_.property.columns == [col]
            return attr_
        except:
            continue
    return None

def key_to_value(obj, key, raw=False):
    """
    Evaluate chained relations against a target object
    """
    from baph.db.orm import ORM

    frags = key.split('.')
    if not raw:
        col_key = frags.pop()
    current_obj = obj
    
    while frags:
        if not current_obj:
            # we weren't able to follow the chain back, one of the 
            # fks was probably optional, and had no value
            return None
        
        attr_name = frags.pop(0)
        previous_obj = current_obj
        previous_cls = type(previous_obj)
        current_obj = getattr(previous_obj, attr_name)

        if current_obj:
            # proceed to next step of the chain
            continue

        # relation was empty, we'll grab the fk and lookup the
        # object manually
        attr = getattr(previous_cls, attr_name)
        prop = attr.property

        related_cls = class_resolver(prop.argument)
        related_col = prop.local_remote_pairs[0][0]
        attr_ = column_to_attr(previous_cls, related_col)
        related_key = attr_.key
        related_val = getattr(previous_obj, related_key)
        if related_val is None:
            # relation and key are both empty: no parent found
            return None

        orm = ORM.get()
        session = orm.sessionmaker()
        current_obj = session.query(related_cls).get(related_val)

    if raw:
        return current_obj

    value = getattr(current_obj, col_key, None)
    if value:
        return str(value)
    return None

def get_related_class_from_attr(attr):
    prop = attr.prop
    related_cls = prop.argument
    return class_resolver(related_cls)

def process_rel(relationship):
    if relationship.is_attribute:
        relationship = relationship.property
    argument = class_resolver(relationship.argument)
    collection = collection_resolver(relationship.collection_class)

    if not collection:
        if relationship.uselist:
            collection = list
        else:
            collection = None # scalar
    return {
        'data_type': argument,
        'collection_class': collection,
        }

def process_proxy(attr):
    '''
    print '\nproxy:', attr
    print '  cls:', attr.owning_class
    print '  local_attr:', attr.local_attr
    print '  collection_class:', attr.collection_class
    print '  scalar:', attr.scalar
    print '  value_attr:', attr.value_attr
    print '  remote_attr:', attr.remote_attr
    '''
    info = process_rel(attr.local_attr)
    collections = [info['collection_class']]
    data_type = info['data_type']

    if isinstance(attr.remote_attr, AssociationProxy):
        info2 = process_proxy(attr.remote_attr)
        collections += info2['collection_class']
        data_type = info2['data_type']
    elif isinstance(attr.remote_attr.prop, ColumnProperty):
        prop = attr.remote_attr.prop
        data_type = prop.columns[0]
    elif isinstance(attr.remote_attr.prop, RelationshipProperty):
        info2 = process_rel(attr.remote_attr)
        collections += [info2['collection_class']]
        data_type = info2['data_type']
    else:
        raise Exception("Can't process field of type '%s'" % type(prop))
    return {
        'collection_class': [c for c in collections if c],
        'data_type': data_type,
        }

def sqla_attr_to_modelfield(key, attr, model):
    prop = attr
    from baph.db.models.base import Model as Base
    from baph.forms.models import fields
    kwargs = field_kwargs_from_attr(key, attr, model)
    auto = kwargs.pop('_auto', None)
    data_type = kwargs.pop('data_type')
    collection_class = kwargs.pop('collection_class', None)
    direction = kwargs.pop('_direction', None)
    to_field = kwargs.pop('_remote_col', None)
    proxy = kwargs.pop('proxy', None)

    if inspect_.isclass(data_type) and issubclass(data_type, Base):
        if collection_class is None:
            # scalar value
            if direction == MANYTOONE:
                kwargs['to'] = data_type
                kwargs['to_field'] = to_field
                if prop.back_populates:
                    kwargs['related_name'] = prop.back_populates
                form_class = modelfields.related.ForeignKey
            else:
                kwargs['to'] = data_type
                kwargs['to_field'] = to_field
                form_class = modelfields.related.OneToOneField
                if prop.back_populates:
                    kwargs['related_name'] = prop.back_populates
        else:
            # collection of values
            kwargs['collection_class'] = [list]
            kwargs['related_class'] = data_type
            form_class = fields.MultiObjectField
    elif collection_class == [list]:
        kwargs['collection_class'] = [list]
        kwargs['related_class'] = data_type
        form_class = fields.MultiObjectField
    else:
        form_class = MODELFIELD_MAP[data_type]

    #if form_class in (modelfields.CharField, modelfields.BooleanField):
    #    kwargs.pop('nullable', None)

    form_field = form_class(**kwargs)
    #assert False
    return form_field

def field_kwargs_from_attr(key, attr, model):
    if attr.is_attribute:
        attr = attr.prop

    if attr.extension_type == ASSOCIATION_PROXY:
        return field_kwargs_from_proxy(key, attr, model)

    if isinstance(attr, ColumnProperty):
        return field_kwargs_from_column(key, attr, model)

    if isinstance(attr, RelationshipProperty):
        return field_kwargs_from_relationship(key, attr, model)

    raise Exception('field_kwargs_from_attr can only be called on'
                    'proxies, columns, and relationships')


def field_kwargs_from_column(key, prop, model):
    #kwargs = {'name': attr.key}
    kwargs = {}
    if prop.is_attribute:
        prop = attr.prop
    col = prop.columns[0]
    kwargs['data_type'] = type(col.type)
    if len(col.proxy_set) == 1:
        # single column
        kwargs['db_column'] = col.name
        kwargs['null'] = col.nullable
        kwargs['_auto'] = col.primary_key \
            and type(col.type) == Integer \
            and col.autoincrement
        if col.default:
            kwargs['default'] = col.default
        if col.unique:
            kwargs['unique'] = col.unique
        if prop.info.get('readonly', False):
            kwargs['editable'] = False
        elif kwargs['_auto']:
            kwargs['editable'] = False
        else:
            kwargs['editable'] = True
        if type(col.type) == Boolean:
            kwargs['blank'] = True
        elif col.default or kwargs['_auto'] or col.nullable:
            kwargs['blank'] = True
        else:
            kwargs['blank'] = False
        if hasattr(col.type, 'length'):
            kwargs['max_length'] = col.type.length
    else:
        # multiple join elements, make it readonly
        kwargs['editable'] = False

    return kwargs

def field_kwargs_from_relationship(key, prop, model):
    if prop.is_attribute:
        prop = attr.prop
    kwargs = process_rel(prop)
    kwargs['null'] = True
    kwargs['editable'] = not prop.viewonly
    kwargs['_direction'] = prop.direction
    remote_col = prop.remote_side.pop()
    kwargs['_remote_col'] = remote_col.name
    kwargs.update(prop.info)
    return kwargs

def field_kwargs_from_proxy(key, attr, model):
    getattr(model, key)
    kwargs = process_proxy(attr)
    kwargs['name'] = key
    kwargs['proxy'] = True
    kwargs['null'] = True
    return kwargs