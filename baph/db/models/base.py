import sys

from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

from baph.core.cache.options import CacheOptions
from baph.db.models.options import Options
from baph.utils.functional import classproperty


class BaseModel(object):
  
  def to_dict(self):
    data = {}
    for attr in inspect(type(self)).column_attrs:
      data[attr.key] = getattr(self, attr.key)
    for key in self._meta.extra_dict_props:
      data[key] = getattr(self, key)
    return data

class ModelBase(DeclarativeMeta):
  """
  Metaclass for all models.
  """
  def add_to_class(cls, name, value):
    if hasattr(value, 'contribute_to_class'):
      value.contribute_to_class(cls, name)
    else:
      setattr(cls, name, value)

  @classproperty
  def base_class(cls):
    """
    Returns the base class of a polymorphic subclass, or the class itself
    if it is not a polymorphic subclass
    """
    for base in cls.__mro__:
      #print '  ', base.__name__
      if base == cls:
        # a class cannot be its own polymorphic base
        continue
      if not issubclass(base, BaseModel):
        # the polymorphic base must be an sqla class
        continue
      if not hasattr(base, '__mapper_args__'):
        # a polymorphic base will have mapper_args
        continue
      if 'polymorphic_on' in base.__mapper_args__:
        return base
    return cls

  def __new__(cls, name, bases, attrs):
    #print '\n%s.__new__(%s)' % (name, cls)
    super_new = super(ModelBase, cls).__new__

    parents = [b for b in bases if isinstance(b, ModelBase) and
      not (b.__name__ == 'Base' and b.__mro__ == (b, object))]
    if not parents:
      return super_new(cls, name, bases, attrs)

    attrs_ = {}
    for key in ('__module__', '__tablename__', '__table_args__',
                '__mapper_args__'):
      if key in attrs:
        attrs_[key] = attrs.pop(key)

    new_class = super_new(cls, name, bases, attrs_)

    attr_meta = attrs.pop('Meta', None)
    if not attr_meta:
      meta = getattr(new_class, 'Meta', None)
    else:
      meta = attr_meta
    base_meta = getattr(new_class, '_meta', None)

    # determine app label
    if getattr(meta, 'app_label', None) is None:
      model_module = sys.modules[new_class.__module__]
      kwargs = {"app_label": model_module.__name__.rsplit('.',1)[0]}
    else:
      kwargs = {}

    new_class.add_to_class('_meta', Options(meta, **kwargs))
    if base_meta:
      for k, v in vars(base_meta).items():
        if not getattr(new_class._meta, k, None):
          setattr(new_class._meta, k, v)

    attr_cache = attrs.pop('Cache', None)
    if not attr_cache:
      cache = getattr(new_class, 'Cache', None)
    else:
      cache = attr_cache
    base_cache = getattr(new_class, '_cache', None)

    new_class.add_to_class('_cache', CacheOptions(cache))
    if base_cache:
      for k, v in vars(base_cache).items():
        if not getattr(new_class._cache, k, None):
          setattr(new_class._cache, k, v)

    # Add all attributes to the class.
    for name, value in attrs.items():
      new_class.add_to_class(name, value)

    return new_class

Model = declarative_base(
  cls=BaseModel,
  metaclass=ModelBase,
  name='Model')
