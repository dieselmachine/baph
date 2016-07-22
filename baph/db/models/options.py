import re

#from baph.utils.translation import (string_concat, get_language, activate,
#    deactivate_all)
from sqlalchemy import inspect, Integer
from sqlalchemy.orm import configure_mappers
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty

from baph.conf import settings
from baph.core.options.base import BaseOptions
from baph.core.cache.options import CacheOptions
#from baph.db.models.fields import Field
#from baph.utils.encoding import force_unicode
from baph.utils.functional import cached_property
from baph.utils.text import camel_case_to_spaces


class Options(BaseOptions):
  propagate = (
    'app_label',
    'filter_translations',
    'latlon_field_names',
    'extra_dict_props',
    'form_class',
    'limit',
    'required_fields',
  )
  defaults = {
    'model_name': None,
    'model_name_plural': None,
    'verbose_name': None,
    'verbose_name_plural': None,
    'app_label': None,
    'swappable': None,
    # filter_translations allows mapping of filter keys to 'full' filters
    # in the event the target column is in another table.
    'filter_translations': {},
    # latlon_field_names is a 2-tuple containing the field names
    # of the latitude and longitude columns (for geocoding purposes)
    'latlon_field_names': None,
    # extra_dict_props contains names of additional properties
    # to be added to the output of instance.to_dict()
    'extra_dict_props': [],
    'form_class': None,
    'limit': 1000,
    # these might not be in use
    'required_fields': None,
  }

  def __init__(self, meta, app_label=None):
    super(Options, self).__init__(meta)
    self.app_label = app_label

  def contribute_to_class(self, cls, name):
    super(Options, self).contribute_to_class(cls, name)

    # First, construct the default values for these options.
    self.object_name = cls.__name__
    self.model_name = self.object_name.lower()
    self.base_model_name = self.model_name
    self.verbose_name = camel_case_to_spaces(self.object_name)

    # initialize params that depend on other params being set
    if self.model_name_plural is None:
      self.model_name_plural = self.model_name + 's'
    self.base_model_name_plural = self.model_name_plural

    if self.verbose_name_plural is None:
      self.verbose_name_plural = self.verbose_name + 's'

    base_class = cls.base_class
    if cls != cls.base_class:
      # this is a polymorphic subclass
      self.base_model_name = base_class._meta.base_model_name
      self.base_model_name_plural = base_class._meta.base_model_name_plural

  @property
  def swapped(self):
    """
    Has this model been swapped out for another? If so, return the model
    name of the replacement; otherwise, return None.
    For historical reasons, model name lookups using get_model() are
    case insensitive, so we make sure we are case insensitive here.
    """
    if self.swappable:
      swapped_for = getattr(settings, self.swappable, None)
      if swapped_for:
        try:
          swapped_label, swapped_object = swapped_for.split('.')
        except ValueError:
          # setting not in the format app_label.model_name
          # raising ImproperlyConfigured here causes problems with
          # test cleanup code - instead it is raised in get_user_model
          # or as part of validation.
          return swapped_for

        if '%s.%s' % (swapped_label, swapped_object.lower()) != self.label_lower:
          return swapped_for
    return None

  @cached_property
  def fields(self):
    """
    The getter for self.fields. This returns the list of field objects
    available to this model (including through parent models).

    Callers are not permitted to modify this list, since it's a reference
    to this instance (not a copy).
    """
    try:
      self._field_name_cache
    except AttributeError:
      self._fill_fields_cache()
    return self._field_name_cache

  def _fill_fields_cache(self):
    cache = []
    if not self.model.__mapper__.configured:
      configure_mappers()
    insp = inspect(self.model)

    for prop in insp.column_attrs + insp.relationships:
      attr = prop.class_attribute
      field = Field.field_from_attr(attr.key, attr, self.model)
      cache.append((field, None))

    for key, attr in insp.all_orm_descriptors.items():
      if attr.extension_type == ASSOCIATION_PROXY:
        attr = getattr(self.model, key)
        field = Field.field_from_attr(key, attr, self.model)
        cache.append((field, None))
    self._field_cache = tuple(cache)
    self._field_name_cache = [x for x, _ in cache]

  def get_field(self, name, many_to_many=True):
    """
    Returns the requested field by name. Raises FieldDoesNotExist on error.
    """
    to_search = self.fields #(self.fields + self.many_to_many) if many_to_many else self.fields
    for f in to_search:
      if f.name == name:
        return f
    raise FieldDoesNotExist('%s has no field named %r' % (self.object_name, name))
