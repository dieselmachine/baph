from __future__ import unicode_literals

from bisect import bisect
from collections import OrderedDict, defaultdict
from itertools import chain

from django.apps import apps
from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from django.db.models.fields import AutoField
from django.db.models.options import make_immutable_fields_list, PROXY_PARENTS
from django.utils import lru_cache
from django.utils.encoding import force_unicode, force_text
from django.utils.functional import cached_property
from django.utils.translation import override, string_concat
from sqlalchemy import inspect, Integer
from sqlalchemy.orm import configure_mappers
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY, HYBRID_METHOD
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty

from baph.apps import apps
from baph.db import types
from baph.db.models.utils import sqla_attr_to_modelfield
from baph.utils.text import camel_case_to_spaces


DEFAULT_NAMES = ('apps', 'model_name', 'model_name_plural',
                 'verbose_name', 'verbose_name_plural', 
                 'app_label', 'swappable', 'auto_created',
                 'cache_alias', 'cache_timeout', 'cache_pointers',
                 'cache_detail_fields', 'cache_list_fields',
                 'cache_relations', 'cache_cascades', 
                 'filter_translations', 'filter_initial',
                 'permissions', 'permission_scopes', 'form_class',
                 'permission_actions', 'permission_classes',
                 'permission_parents', 'permission_full_parents', 
                 'permission_limiters', 'permission_terminator',
                 'permission_handler', 'permission_resources',
                 'action_pk', 'actions',
                 'list_actions', 'detail_actions',
                 'filtering', 'ordering', 'searchable',
                 'global_column', 'global_cascades', 'global_parents',
                 'virtual_fields', 'extension_field',
                 'extension_owner_field',
                 'labels', 'help_texts',
                 )

def normalize_together(option_together):
    """
    option_together can be either a tuple of tuples, or a single
    tuple of two strings. Normalize it to a tuple of tuples, so that
    calling code can uniformly expect that.
    """
    try:
        if not option_together:
            return ()
        if not isinstance(option_together, (tuple, list)):
            raise TypeError
        first_element = next(iter(option_together))
        if not isinstance(first_element, (tuple, list)):
            option_together = (option_together,)
        # Normalize everything to tuples
        return tuple(tuple(ot) for ot in option_together)
    except TypeError:
        # If the value of option_together isn't valid, return it
        # verbatim; this will be picked up by the check framework later.
        return option_together

class Options(object):
    FORWARD_PROPERTIES = ('fields', 'many_to_many', 'concrete_fields',
                          'local_concrete_fields', '_forward_fields_map')
    REVERSE_PROPERTIES = ('related_objects', 'fields_map', '_relation_tree')

    def __init__(self, meta, app_label=None):
        # current django stuff
        self._get_fields_cache = {}
        self.local_fields = []
        self.local_many_to_many = []
        self.virtual_fields = []
        self.model_name = None
        self.verbose_name = None
        self.verbose_name_plural = None
        #self.db_table = ''
        self.ordering = []
        #self._ordering_clash = False
        #self.unique_together = []
        #self.index_together = []
        #self.select_on_save = False
        #self.default_permissions = ('add', 'change', 'delete')
        #self.permissions = []
        self.object_name = None
        self.app_label = app_label
        self.get_latest_by = None
        self.order_with_respect_to = None
        #self.db_tablespace = settings.DEFAULT_TABLESPACE
        #self.required_db_features = []
        #self.required_db_vendor = None
        self.meta = meta
        self.pk = None
        self.has_auto_field = False
        #self.auto_field = None
        self.abstract = False
        #self.managed = True
        self.proxy = False
        #self.proxy_for_model = None
        #self.concrete_model = None
        self.swappable = None
        self.parents = OrderedDict()
        self.auto_created = False
        self.managers = []
        #self.related_fkey_lookups = []
        self.apps = apps
        self.default_related_name = None

        # old django stuff
        self.proxied_children = []

        # baph stuff
        self.django_descriptors = object()
        self.model_name_plural = None
        self.base_model_name = None
        self.base_model_name_plural = None
        self.form_class = None
        self._modelfield_cache = {}
        self.searchable = []

        self.cache_alias = DEFAULT_CACHE_ALIAS
        self.cache_timeout = None
        self.cache_detail_fields = []
        self.cache_list_fields = []
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
        # global_column is the name of the boolean column which indicates
        # global status. This must be set in order to use globalization
        self.global_column = None
        # global_cascades is a list of relationships through which 
        # globalization should propagate (all children become globals)
        self.global_cascades = []
        # global_parents is a list of relationships which should be checked
        # on object creation, and if a global parent is found, the new
        # object will be globalized
        self.global_parents = []

        self.filtering = []
        # filter_translations allows mapping of filter keys to 'full' filters
        # in the event the target column is in another table.
        self.filter_translations = {}
        self.filter_initial = {}
        
        self.permissions = {}
        self.permission_scopes = {}
        # permission_parents is a list of *toOne relations which can be
        # considered to refer to 'parents'. These relations will automatically
        # be considered when generating possible permission paths
        self.permission_parents = []
        # permission_resources is a dict, with each key containing a resource
        # name to expose (generally the lowercased classname), and a value 
        # containing a list of actions available on that resource
        # ex: { 'image': ['add', 'edit', 'delete', 'view', 'crop'] }
        self.permission_resources = {}
        # permission_handler is the name of the parent relation through which
        # to route permission requests for this object
        self.permission_handler = None
        # permission_limiters is a dict, with each key containing an 'alias'
        # for the limiter, used in generating codenames. Each value is a dict,
        # with the key referring to the local column to be checked, and the
        # value containing an expression which will be evaluated against the
        # permission's context
        self.permission_limiters = {}
        self.permission_full_parents = []
        self.permission_terminator = False

        self.detail_actions = []
        self.list_actions = []
        self.labels = {}
        self.help_texts = {}
        self.extension_field = None
        self.extension_owner_field = None
        self.limit = 1000
        
        #self.required_fields = None

    @property
    def label(self):
        return '%s.%s' % (self.app_label, self.object_name)

    @property
    def label_lower(self):
        return '%s.%s' % (self.app_label, self.model_name)

    @property
    def app_config(self):
        # Don't go through get_app_config to avoid triggering imports.
        return self.apps.app_configs.get(self.app_label)

    @property
    def installed(self):
        return self.app_config is not None

    def contribute_to_class(self, cls, name):
        from django.db import connection
        from django.db.backends.utils import truncate_name

        cls._meta = self
        self.model = cls
        # First, construct the default values for these options.
        self.object_name = cls.__name__
        self.model_name = self.object_name.lower()
        self.verbose_name = camel_case_to_spaces(self.object_name)

        # Store the original user-defined values for each option,
        # for use when serializing the model definition
        self.original_attrs = {}

        # Next, apply any overridden values from 'class Meta'.
        if self.meta:
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
                    self.original_attrs[attr_name] = getattr(self, attr_name)
                elif hasattr(self.meta, attr_name):
                    setattr(self, attr_name, getattr(self.meta, attr_name))
                    self.original_attrs[attr_name] = getattr(self, attr_name)

            #self.unique_together = normalize_together(self.unique_together)
            #self.index_together = normalize_together(self.index_together)

            # verbose_name_plural is a special case because it uses a 's'
            # by default.
            if self.verbose_name_plural is None:
                self.verbose_name_plural = string_concat(self.verbose_name, 's')

            # order_with_respect_and ordering are mutually exclusive.
            self._ordering_clash = bool(self.ordering and self.order_with_respect_to)

            # Any leftover attributes must be invalid.
            if meta_attrs != {}:
                raise TypeError("'class Meta' got invalid attribute(s): %s" 
                    % ','.join(meta_attrs.keys()))
        else:
            self.verbose_name_plural = string_concat(self.verbose_name, 's')

        # initialize params that depend on other params being set
        if self.model_name_plural is None:
            self.model_name_plural = self.model_name + 's'

        if self.cache_timeout is None:
            self.cache_timeout = caches[self.cache_alias].default_timeout

        from baph.db.models.base import Model as Base

        base_model_name = self.model_name
        base_model_name_plural = self.model_name_plural
        for base in self.model.__mro__:
            if not issubclass(base, Base):
                continue
            if base in (self.model, Base):
                continue
            if not hasattr(base, '__mapper_args__'):
                continue
            if 'polymorphic_on' in base.__mapper_args__:
                base_model_name = base._meta.base_model_name
                base_model_name_plural = base._meta.base_model_name_plural
                break
        self.base_model_name = unicode(base_model_name)
        self.base_model_name_plural = unicode(base_model_name_plural)

        del self.meta

    def _prepare(self, model):
        if self.order_with_respect_to:
            # The app registry will not be ready at this point, so we cannot
            # use get_field().
            query = self.order_with_respect_to
            try:
                self.order_with_respect_to = next(
                    f for f in self._get_fields(reverse=False)
                    if f.name == query or f.attname == query
                )
            except StopIteration:
                raise FieldDoesNotExist('%s has no field named %r' % (self.object_name, query))

            self.ordering = ('_order',)
            if not any(isinstance(field, OrderWrt) for field in model._meta.local_fields):
                model.add_to_class('_order', OrderWrt())
        else:
            self.order_with_respect_to = None

        if self.pk is None:
            if self.parents:
                # Promote the first parent link in lieu of adding yet another
                # field.
                field = next(six.itervalues(self.parents))
                # Look for a local field with the same name as the
                # first parent link. If a local field has already been
                # created, use it instead of promoting the parent
                already_created = [fld for fld in self.local_fields \
                    if fld.name == field.name]
                if already_created:
                    field = already_created[0]
                field.primary_key = True
                self.setup_pk(field)
            else:
                auto = AutoField(verbose_name='ID', primary_key=True,
                        auto_created=True)
                model.add_to_class('id', auto)

    def add_field(self, field, virtual=False):
        # Insert the given field in the order in which it was created, using
        # the "creation_counter" attribute of the field.
        # Move many-to-many related fields from self.fields into
        # self.many_to_many.
        if virtual:
            self.virtual_fields.append(field)
        elif field.is_relation and field.many_to_many:
            self.local_many_to_many.insert(bisect(self.local_many_to_many, field), field)
        else:
            self.local_fields.insert(bisect(self.local_fields, field), field)
            self.setup_pk(field)

        # If the field being added is a relation to another known field,
        # expire the cache on this field and the forward cache on the field
        # being referenced, because there will be new relationships in the
        # cache. Otherwise, expire the cache of references *to* this field.
        # The mechanism for getting at the related model is slightly odd -
        # ideally, we'd just ask for field.related_model. However, related_model
        # is a cached property, and all the models haven't been loaded yet, so
        # we need to make sure we don't cache a string reference.
        if field.is_relation and hasattr(field.rel, 'to') and field.rel.to:
            try:
                field.rel.to._meta._expire_cache(forward=False)
            except AttributeError:
                pass
            self._expire_cache()
        else:
            self._expire_cache(reverse=False)

    def setup_pk(self, field):
        if not self.pk and field.primary_key:
            self.pk = field
            field.serialize = False

    @property
    def verbose_name_raw(self):
        """
        There are a few places where the untranslated verbose name is needed
        (so that we get the same value regardless of currently active
        locale).
        """
        with override(None):
            return force_text(self.verbose_name)

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

                if '%s.%s' % (swapped_label, swapped_object.lower()) != self.label_lower():
                    return swapped_for
        return None

    @lru_cache.lru_cache(maxsize=None)
    def all_fields(self, org_id=None):
        self.generate_modelfields(org_id)
        is_not_an_m2m_field = lambda f: not (f.is_relation and f.many_to_many)
        is_not_a_generic_relation = lambda f: not (f.is_relation 
            and f.one_to_many)
        is_not_a_generic_foreign_key = lambda f: not (f.is_relation 
            and f.many_to_one 
            and not (hasattr(f.rel, 'to') and f.rel.to))
        return make_immutable_fields_list(
            "fields",
            (f for f in self._get_fields(reverse=False) 
                if is_not_an_m2m_field(f) 
                and is_not_a_generic_relation(f)
                and is_not_a_generic_foreign_key(f))
        )

    @property
    def fields(self):
        """
        The getter for self.fields. This returns the list of field objects
        available to this model (including through parent models).

        Callers are not permitted to modify this list, since it's a reference
        to this instance (not a copy).
        """
        from baph.middleware.threadlocals import get_current_organization
        org = get_current_organization()
        if org:
            return self.all_fields(org.id)
        return self.all_fields()

    @cached_property
    def concrete_fields(self):
        """
        Returns a list of all concrete fields on the model and its parents.
        Private API intended only to be used by Django itself; get_fields()
        combined with filtering of field properties is the public API for
        obtaining this field list.
        """
        return make_immutable_fields_list(
            "concrete_fields", 
            (f for f in self.fields if f.concrete)
        )

    @cached_property
    def local_concrete_fields(self):
        """
        Returns a list of all concrete fields on the model.
        Private API intended only to be used by Django itself; get_fields()
        combined with filtering of field properties is the public API for
        obtaining this field list.
        """
        return make_immutable_fields_list(
            "local_concrete_fields", 
            (f for f in self.local_fields if f.concrete)
        )

    @cached_property
    def many_to_many(self):
        """
        Returns a list of all many to many fields on the model and its parents.
        Private API intended only to be used by Django itself; get_fields()
        combined with filtering of field properties is the public API for
        obtaining this list.
        """
        return make_immutable_fields_list(
            "many_to_many",
            (f for f in self._get_fields(reverse=False)
            if f.is_relation and f.many_to_many)
        )

    @cached_property
    def _forward_fields_map(self):
        res = {}
        fields = self._get_fields(reverse=False)
        for field in fields:
            res[field.name] = field
            # Due to the way Django's internals work, get_field() should also
            # be able to fetch a field by attname. In the case of a concrete
            # field with relation, includes the *_id name too
            try:
                res[field.attname] = field
            except AttributeError:
                pass
        return res

    def generate_modelfields(self, org_id):
        modelfields = {}
        for field in self.model.get_fields():
            key = field.key
            #print (key, field)
            modelfield = sqla_attr_to_modelfield(key, field, self.model)
            modelfield.contribute_to_class(self.model, key)
            modelfields[key] = modelfield
        self._modelfield_cache = modelfields
        return modelfields

    def get_field(self, field_name):
        """
        Return a field instance given the name of a forward or reverse field.
        """
        try:
            # In order to avoid premature loading of the relation tree
            # (expensive) we prefer checking if the field is a forward field.
            return self._forward_fields_map[field_name]
        except KeyError:
            # If the app registry is not ready, reverse fields are
            # unavailable, therefore we throw a FieldDoesNotExist exception.
            if not self.apps.models_ready:
                raise FieldDoesNotExist(
                    "%s has no field named %r. The app cache isn't ready yet, "
                    "so if this is an auto-created related field, it won't "
                    "be available yet." % (self.object_name, field_name)
                )

        try:
            # Retrieve field instance by name from cached or just-computed
            # field map.
            return self.fields_map[field_name]
        except KeyError:
            raise FieldDoesNotExist('%s has no field named %r' % 
                (self.object_name, field_name))

    def _expire_cache(self, forward=True, reverse=True):
        # This method is usually called by apps.cache_clear(), when the
        # registry is finalized, or when a new field is added.
        properties_to_expire = []
        if forward:
            properties_to_expire.extend(self.FORWARD_PROPERTIES)
        if reverse and not self.abstract:
            properties_to_expire.extend(self.REVERSE_PROPERTIES)

        for cache_key in properties_to_expire:
            try:
                delattr(self, cache_key)
            except AttributeError:
                pass

        self._get_fields_cache = {}

    def get_fields(self, include_parents=True, include_hidden=False):
        """
        Returns a list of fields associated to the model. By default, includes
        forward and reverse fields, fields derived from inheritance, but not
        hidden fields. The returned fields can be changed using the parameters:
        - include_parents: include fields derived from inheritance
        - include_hidden:  include fields that have a related_name that
                           starts with a "+"
        """
        if include_parents is False:
            include_parents = PROXY_PARENTS
        return self._get_fields(include_parents=include_parents,
                                include_hidden=include_hidden)

    def _get_fields(self, forward=True, reverse=True, include_parents=True,
                    include_hidden=False, seen_models=None):
        """
        Internal helper function to return fields of the model.
        * If forward=True, then fields defined on this model are returned.
        * If reverse=True, then relations pointing to this model are returned.
        * If include_hidden=True, then fields with is_hidden=True are returned.
        * The include_parents argument toggles if fields from parent models
          should be included. It has three values: True, False, and
          PROXY_PARENTS. When set to PROXY_PARENTS, the call will return all
          fields defined for the current model or any of its parents in the
          parent chain to the model's concrete model.
        """
        if include_parents not in (True, False, PROXY_PARENTS):
            raise TypeError("Invalid argument for include_parents: %s" % 
                (include_parents,))
        # This helper function is used to allow recursion in ``get_fields()``
        # implementation and to provide a fast way for Django's internals to
        # access specific subsets of fields.

        # We must keep track of which models we have already seen. Otherwise we
        # could include the same field multiple times from different models.
        topmost_call = False
        if seen_models is None:
            seen_models = set()
            topmost_call = True
        seen_models.add(self.model)

        # Creates a cache key composed of all arguments
        cache_key = (forward, reverse, include_parents, include_hidden, 
                     topmost_call)

        try:
            # In order to avoid list manipulation. Always return a shallow copy
            # of the results.
            return self._get_fields_cache[cache_key]
        except KeyError:
            pass

        fields = []
        # Recursively call _get_fields() on each parent, with the same
        # options provided in this call.
        if include_parents is not False:
            for parent in self.parents:
                # In diamond inheritance it is possible that we see the same
                # model from two different routes. In that case, avoid adding
                # fields from the same parent again.
                if parent in seen_models:
                    continue
                if (parent._meta.concrete_model != self.concrete_model and
                        include_parents == PROXY_PARENTS):
                    continue
                for obj in parent._meta._get_fields(
                        forward=forward, reverse=reverse, 
                        include_parents=include_parents, 
                        include_hidden=include_hidden, 
                        seen_models=seen_models):
                    if hasattr(obj, 'parent_link') and obj.parent_link:
                        continue
                    fields.append(obj)
        if reverse:
            # Tree is computed once and cached until the app cache is expired.
            # It is composed of a list of fields pointing to the current model
            # from other models.
            all_fields = self._relation_tree
            for field in all_fields:
                # If hidden fields should be included or the relation is not
                # intentionally hidden, add to the fields dict.
                if include_hidden or not field.remote_field.hidden:
                    fields.append(field.remote_field)

        if forward:
            fields.extend(
                field for field in chain(self.local_fields, self.local_many_to_many)
            )
            # Virtual fields are recopied to each child model, and they get a
            # different model as field.model in each child. Hence we have to
            # add the virtual fields separately from the topmost call. If we
            # did this recursively similar to local_fields, we would get field
            # instances with field.model != self.model.
            if topmost_call:
                fields.extend(
                    f for f in self.virtual_fields
                )

        # add custom fields
        from baph.middleware.threadlocals import get_current_organization
        org = get_current_organization()
        if org:
            for f in self.model.get_custom_fields(org.id):
                fields.append(f)

        # In order to avoid list manipulation. Always
        # return a shallow copy of the results
        fields = make_immutable_fields_list("get_fields()", fields)
        # Store result into cache for later access
        self._get_fields_cache[cache_key] = fields
        return fields