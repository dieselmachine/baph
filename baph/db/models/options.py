import re
from types import FunctionType

from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.translation import (string_concat, get_language, activate,
    deactivate_all)
from sqlalchemy import inspect, Integer
from sqlalchemy.orm import configure_mappers
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty

from baph.db.models.fields import ModelField
from baph.db import types
from baph.utils.functional import cached_property


get_verbose_name = lambda class_name: \
    re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name) \
        .lower().strip()

DEFAULT_NAMES = ('verbose_name', 'verbose_name_plural', 
                 'app_label', 'swappable', 'auto_created',
                 'cache_detail_keys', 'cache_list_keys', 'cache_pointers',
                 'cache_relations', 'cache_cascades', 
                 'permissions', 'permission_scopes', 'form_class',
                 )
'''                 
                 'permission_actions', 'permission_classes',
                 'permission_parents', 'permission_values',
                 'permission_column', 'permission_terminator',
                 'permission_pk_kwarg')
'''
#DEFAULT_ACTIONS = ['add', 'view', 'edit', 'delete']

class Options(object):
    def __init__(self, meta, app_label=None):
        # cache_detail_keys are primary cache keys which are invalidated
        # anytime the object changes. Because this key cannot exist prior
        # to create of the object, these are not processed during CREATE.
        # format: (cache_key_template, columns)
        # cache_key_template is a string, with placeholders for formatting
        # using data from the instance (ex: businesses:detail:id=%(id)s)
        # columns is a list of columns to monitor for changes (ex: ['city'])
        # the key will only be invalidated if at least one specified column
        # has changed, or columns is None
        self.cache_detail_keys = []
        # cache_list_keys are keys for lists of objects. These keys are not
        # singular keys, but "version keys", which are bases for multiple
        # subsets of the base set (subsets being caused by filters or searches)
        # format: (cache_key_template, columns) (same as above)
        # when invalidated, rather than deleting the key, the key is
        # incremented, so all subsets attempting to use the contained value
        # for key generation will be invalidated at once
        self.cache_list_keys = []
        # cache_pointers is a list of identity keys which contain no data
        # other than the primary key of the object being pointed at.
        # format: (cache_key_template, columns, name)
        # cache_key_template and columns function as above, and 'name' is
        # an alias to help distinguish between keys during unittesting
        # when an update occurs, two actions occur: the new value is set
        # to the current object, and the previous value (if different) is
        # set to False (not deleted)
        self.cache_pointers = []
        # cache_relations is a list of relations which should be monitored
        # for changes when generating cache keys for invalidation. This should
        # be used for relationships to composite keys, which cannot be
        # handled properly via cache_cascades
        self.cache_relations = []
        # cache_cascades is a list of relations through which to cascade
        # invalidations. Use this when an object is cached as a subobject of
        # a larger cache, to signal the parent that it needs to recache
        self.cache_cascades = []
        '''
        self.permission_actions = []
        self.permission_classes = []
        self.permission_parents = []
        self.permission_values = {}
        self.permission_terminator = False
        self.permission_column = None
        self.permission_pk_kwarg = None
        '''
        self.limit = 1000
        self.model_name, self.model_name_plural = None, None
        self.verbose_name, self.verbose_name_plural = None, None
        self.permissions = {}
        self.permission_scopes = {}
        self.object_name, self.app_label = None, app_label
        self.pk = None
        self.form_class = None
        self.meta = meta

        self.swappable = None
        self.auto_created = False
        self.required_fields = None

    def contribute_to_class(self, cls, name):
        cls._meta = self
        self.model = cls
        self.installed = re.sub('\.models$', '', cls.__module__) \
            in settings.INSTALLED_APPS
        # First, construct the default values for these options.
        self.object_name = cls.__name__
        self.model_name = self.object_name.lower()
        self.model_name_plural = self.model_name + 's'
        self.verbose_name = get_verbose_name(self.object_name)
        '''
        # permission-related stuff
        for action in DEFAULT_ACTIONS:
            if not action in self.permission_actions:
                self.permission_actions.append(action)
        if not self.permission_classes:
            self.permission_classes = [self.model_name]
        if hasattr(cls, '__mapper__') and len(cls.__mapper__.primary_key) == 1:
            if not self.permission_pk_kwarg:
                self.permission_pk_kwarg = '%s_id' % self.model_name
        else:
            self.permission_pk_kwarg = None
        '''
        # Next, apply any overridden values from 'class Meta'.
        if getattr(self, 'meta', None):
            meta_attrs = self.meta.__dict__.copy()
            for name in self.meta.__dict__:
                # Ignore any private attributes that Django doesn't care about.
                # NOTE: We can't modify a dictionary's contents while looping
                # over it, so we loop over the *original* dictionary instead.
                if name.startswith('_'):
                    del meta_attrs[name]
            for attr_name in DEFAULT_NAMES:
                if attr_name in meta_attrs:
                    setattr(self, attr_name, meta_attrs.pop(attr_name))
                elif hasattr(self.meta, attr_name):
                    setattr(self, attr_name, getattr(self.meta, attr_name))

            # verbose_name_plural is a special case because it uses a 's'
            # by default.
            if self.verbose_name_plural is None:
                self.verbose_name_plural = string_concat(self.verbose_name, 's')

            # Any leftover attributes must be invalid.
            if meta_attrs != {}:
                raise TypeError("'class Meta' got invalid attribute(s): %s" % ','.join(meta_attrs.keys()))
            del self.meta
        else:
            self.verbose_name_plural = string_concat(self.verbose_name, 's')
        
        
    def verbose_name_raw(self):
        """
        There are a few places where the untranslated verbose name is needed
        (so that we get the same value regardless of currently active
        locale).
        """
        lang = get_language()
        deactivate_all()
        raw = force_unicode(self.verbose_name)
        activate(lang)
        return raw
    verbose_name_raw = property(verbose_name_raw)

    def _swapped(self):
        """
        Has this model been swapped out for another? If so, return the model
        name of the replacement; otherwise, return None.

        For historical reasons, model name lookups using get_model() are
        case insensitive, so we make sure we are case insensitive here.
        """
        if self.swappable:
            model_label = '%s.%s' % (self.app_label, self.model_name)
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

                if '%s.%s' % (swapped_label, swapped_object.lower()) not in (None, model_label):
                    return swapped_for
        return None
    swapped = property(_swapped)
    '''
    def kwargs_from_hybrid(self, attr):
        kwargs = {}
        expr = attr.expr(self.model)
        kwargs['data_type'] = type(expr.type)
        kwargs['readonly'] = not attr.fset
        return kwargs

    def kwargs_from_column_attr(self, attr):
        kwargs = {}
        col = attr.property.columns[0]
        kwargs['data_type'] = type(col.type)
        if len(col.proxy_set) == 1:
            # single column
            kwargs['auto'] = col.primary_key \
                and type(col.type) == Integer \
                and col.autoincrement
            kwargs['default'] = col.default
            kwargs['nullable'] = col.nullable
            kwargs['unique'] = col.unique
            kwargs['readonly'] = attr.info.get('readonly', False)
        else:
            # multiple join elements, make it readonly
            kwargs['readonly'] = True
        return kwargs

    def kwargs_from_relation_attr(self, attr):
        prop = attr.property
        kwargs = {}
        data_type = prop.argument
        if isinstance(data_type, FunctionType):
            # lazy-loaded attr that hasn't been evaluated yet
            data_type = data_type()
        elif getattr(data_type, 'is_mapper', False):
            data_type = data_type.class_

        data_collection = prop.collection_class
        if isinstance(data_collection, FunctionType):
            # lambda-based evaluator, call it and check the type
            data_collection = type(data_collection())

        kwargs['data_type'] = data_type
        kwargs['data_collection'] = data_collection
        kwargs['uselist'] = prop.uselist
        kwargs['readonly'] = prop.viewonly
        kwargs['local'] = False
        return kwargs

    def kwargs_from_proxy(self, key, attr):
        proxy = getattr(self.model, key)
        attr = self.get_attr_from_proxy(proxy)
        prop = attr.property
        if isinstance(prop, ColumnProperty):
            kwargs = self.kwargs_from_column_attr(attr)
        elif isinstance(prop, RelationshipProperty):
            kwargs = self.kwargs_from_relation_attr(attr)
        data_collection = proxy.local_attr.property.collection_class
        if data_collection:
            data_collection = type(data_collection())
        kwargs['data_collection'] = data_collection
        kwargs['local'] = False
        return kwargs

    def _fill_fields_cache(self):
        cache = []
        if not self.model.__mapper__.configured:
            configure_mappers()
        for key, attr in inspect(self.model).all_orm_descriptors.items():
            if attr.is_mapper:
                continue
            elif attr.extension_type == HYBRID_METHOD:
                continue
            elif attr.extension_type == HYBRID_PROPERTY:
                kwargs = self.kwargs_from_hybrid(attr)
            elif attr.extension_type == ASSOCIATION_PROXY:
                kwargs = self.kwargs_from_proxy(key, attr)
            elif isinstance(attr.property, ColumnProperty):
                kwargs = self.kwargs_from_column_attr(attr)
            elif isinstance(attr.property, RelationshipProperty):
                kwargs = self.kwargs_from_relation_attr(attr)
                
            field = ModelField(key, **kwargs)
            cache.append((key, field))
        self._field_cache = tuple(cache)
        self._field_name_cache = [x for x, _ in cache]

    @cached_property
    def fields(self):
        """
        Returns tuple of (key, ModelField) tuples representing available fields
        """
        try:
            self._field_cache
        except AttributeError:
            self._fill_fields_cache()
        return self._field_cache

    @cached_property
    def field_names(self):
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

    def get_attr_from_proxy(cls, proxy):
        if proxy.remote_attr.extension_type == ASSOCIATION_PROXY:
            return cls.get_attr_from_proxy(proxy.remote_attr)
        return proxy.remote_attr
    '''
