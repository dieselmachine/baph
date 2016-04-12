import collections
from itertools import tee
#from types import FunctionType

from django import forms
#from django.core import validators
from django.utils.encoding import smart_text, force_text, force_bytes
from django.utils.text import capfirst
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import *
#from sqlalchemy.ext.declarative.clsregistry import _class_resolver
from sqlalchemy.ext.hybrid import *
#from sqlalchemy.ext.orderinglist import OrderingList
#from sqlalchemy.orm.collections import MappedCollection
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.util import identity_key

from baph.db import types
#from baph.forms import fields

"""
FIELD_MAP = {
    String:         forms.CharField,
    Text:           forms.CharField,
    Unicode:        forms.CharField,
    UnicodeText:    forms.CharField,
    Integer:        forms.IntegerField,
    Float:          forms.FloatField,
    DateTime:       forms.DateTimeField,
    Date:           forms.DateField,
    Time:           forms.TimeField,
    Boolean:        forms.BooleanField,
    }
'''
    types.Json:     fields.JsonField,
    types.List:     fields.ListField,
    types.Dict:     fields.DictField,
    object:        fields.ObjectField,
    }
'''
COLLECTION_MAP = {
    OrderingList:   types.List,
    MappedCollection:   types.Dict,
    }
"""
class NOT_PROVIDED:
    pass

from django.core.files.base import File
from django.db.models.fields import files, related
from django.utils import six
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.base import instance_state, instance_dict

class FileDescriptor(InstrumentedAttribute, files.FileDescriptor):

    def __init__(self, field):
        attr = getattr(field.model, field.name)
        super(FileDescriptor, self).__init__(attr.class_, attr.key,
            impl=attr.impl, comparator=attr.comparator,
            parententity=attr._parententity, of_type=attr._of_type)
        self.field = field

    def __set__(self, instance, value):
        InstrumentedAttribute.__set__(self, instance, value)

    def __get__(self, instance, owner):
        print '__get__'
        if instance is None:
            return self
        return files.FileDescriptor.__get__(self, instance, owner)

        dict_ = instance_dict(instance)
        if self._supports_population and self.key in dict_:
            file = dict_[self.key]
        else:
            file = self.impl.get(instance_state(instance), dict_)

        # This is slightly complicated, so worth an explanation.
        # instance.file`needs to ultimately return some instance of `File`,
        # probably a subclass. Additionally, this returned object needs to have
        # the FieldFile API so that users can easily do things like
        # instance.file.path and have that delegated to the file storage engine.
        # Easy enough if we're strict about assignment in __set__, but if you
        # peek below you can see that we're not. So depending on the current
        # value of the field we have to dynamically construct some sort of
        # "thing" to return.

        # The instance dict contains whatever was originally assigned
        # in __set__.
        #file = instance.__dict__[self.field.name]

        # If this value is a string (instance.file = "path/to/file") or None
        # then we simply wrap it with the appropriate attribute class according
        # to the file field. [This is FieldFile for FileFields and
        # ImageFieldFile for ImageFields; it's also conceivable that user
        # subclasses might also want to subclass the attribute class]. This
        # object understands how to convert a path to a file, and also how to
        # handle None.
        if isinstance(file, six.string_types) or file is None:
            attr = self.field.attr_class(instance, self.field, file)
            instance.__dict__[self.field.name] = attr

        # Other types of files may be assigned as well, but they need to have
        # the FieldFile interface added to them. Thus, we wrap any other type of
        # File inside a FieldFile (well, the field's attr_class, which is
        # usually FieldFile).
        elif isinstance(file, File) and not isinstance(file, files.FieldFile):
            file_copy = self.field.attr_class(instance, self.field, file.name)
            file_copy.file = file
            file_copy._committed = False
            instance.__dict__[self.field.name] = file_copy

        # Finally, because of the (some would say boneheaded) way pickle works,
        # the underlying FieldFile might not actually itself have an associated
        # file. So we need to reset the details of the FieldFile in those cases.
        elif isinstance(file, files.FieldFile) and not hasattr(file, 'field'):
            file.instance = instance
            file.field = self.field
            file.storage = self.field.storage

        # That was fun, wasn't it?
        return instance.__dict__[self.field.name]


    '''
    def __set__(self, instance, value):
        self.impl.set(instance_state(instance),
                      instance_dict(instance), value, None)

    def __delete__(self, instance):
        self.impl.delete(instance_state(instance), instance_dict(instance))

    def __get__(self, instance, owner):
        if instance is None:
            return self

        dict_ = instance_dict(instance)
        if self._supports_population and self.key in dict_:
            return dict_[self.key]
        else:
            return self.impl.get(instance_state(instance), dict_)


    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            return self

        # This is slightly complicated, so worth an explanation.
        # instance.file`needs to ultimately return some instance of `File`,
        # probably a subclass. Additionally, this returned object needs to have
        # the FieldFile API so that users can easily do things like
        # instance.file.path and have that delegated to the file storage engine.
        # Easy enough if we're strict about assignment in __set__, but if you
        # peek below you can see that we're not. So depending on the current
        # value of the field we have to dynamically construct some sort of
        # "thing" to return.

        # The instance dict contains whatever was originally assigned
        # in __set__.
        file = instance.__dict__[self.field.name]

        # If this value is a string (instance.file = "path/to/file") or None
        # then we simply wrap it with the appropriate attribute class according
        # to the file field. [This is FieldFile for FileFields and
        # ImageFieldFile for ImageFields; it's also conceivable that user
        # subclasses might also want to subclass the attribute class]. This
        # object understands how to convert a path to a file, and also how to
        # handle None.
        if isinstance(file, six.string_types) or file is None:
            attr = self.field.attr_class(instance, self.field, file)
            instance.__dict__[self.field.name] = attr

        # Other types of files may be assigned as well, but they need to have
        # the FieldFile interface added to them. Thus, we wrap any other type of
        # File inside a FieldFile (well, the field's attr_class, which is
        # usually FieldFile).
        elif isinstance(file, File) and not isinstance(file, FieldFile):
            file_copy = self.field.attr_class(instance, self.field, file.name)
            file_copy.file = file
            file_copy._committed = False
            instance.__dict__[self.field.name] = file_copy

        # Finally, because of the (some would say boneheaded) way pickle works,
        # the underlying FieldFile might not actually itself have an associated
        # file. So we need to reset the details of the FieldFile in those cases.
        elif isinstance(file, FieldFile) and not hasattr(file, 'field'):
            file.instance = instance
            file.field = self.field
            file.storage = self.field.storage

        # That was fun, wasn't it?
        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
    '''

class ForeignKey(related.ForeignKey):
    def get_attname(self):
        return self.db_column

class FileField(files.FileField):
    descriptor_class = FileDescriptor

class ImageField(files.ImageField):
    descriptor_class = FileDescriptor    

    #def get_prep_lookup(self, lookup_type, value):
    #    assert False

    #def get_prep_value(self, value):
    #    v = super(ImageField, self).get_prep_value(value)
    #    assert False

"""
def get_related_class_from_attr(attr):
    prop = attr.property
    related_cls = prop.argument
    if isinstance(related_cls, FunctionType):
        # lazy-loaded Model
        related_cls = related_cls()
    if hasattr(related_cls, 'is_mapper') and related_cls.is_mapper:
        # we found a mapper, grab the class from it
        related_cls = related_cls.class_
    if isinstance(related_cls, _class_resolver):
        related_cls = related_cls()
    return related_cls
"""
"""
def normalize_collection_class(collection_class):
    if isinstance(collection_class, FunctionType):
        # lambda-based evaluator, call it and check the type
        collection_class = type(collection_class())
    if collection_class is None:
        return None
    if collection_class in (dict, MappedCollection):
        return dict
    if collection_class in (set, list, OrderingList):
        return list
    raise Exception('Unknown collection_class: %s' % collection_class)
"""
class Field(object):

    creation_counter = 0
    auto_creation_counter = -1

    def __init__(self, verbose_name=None, name=None, primary_key=False, 
                  unique=False, blank=False, nullable=False, editable=True, 
                  default=None, data_type=None, auto_created=False,
                  auto=False, collection_class=None, proxy=False,
                  help_text='', choices=None, uselist=False, required=False,
                  max_length=None, attname=None
                ):
        self.name = name
        self.attname = name
        self.verbose_name = verbose_name or capfirst(self.name)
        self.primary_key = primary_key
        self._unique = unique
        self.blank, self.nullable = blank, nullable
        self.default = default
        self.editable = editable
        self.help_text = help_text
        self._choices = choices or []
        self.data_type = data_type
        self.collection_class = collection_class
        self.uselist = uselist
        self.required = required
        self.max_length = max_length

        # Adjust the appropriate creation counter, and save our local copy.
        if auto_created:
            self.creation_counter = Field.auto_creation_counter
            Field.auto_creation_counter -= 1
        else:
            self.creation_counter = Field.creation_counter
            Field.creation_counter += 1

    @property
    def unique(self):
        return self._unique or self.primary_key

    def _get_choices(self):
        if isinstance(self._choices, collections.Iterator):
            choices, self._choices = tee(self._choices)
            return choices
        else:
            return self._choices
    choices = property(_get_choices)

    def has_default(self):
        """
        Returns a boolean of whether this field has a default value.
        """
        return self.default is not NOT_PROVIDED

    def get_default(self):
        """
        Returns the default value for this field.
        """
        if self.has_default():
            if callable(self.default):
                return self.default()
            return force_text(self.default, strings_only=True)
        return None

    
    def pre_save(self, model_instance, add):
        """
        Returns field's value just before saving.
        """
        return getattr(model_instance, self.attname)

    def save_form_data(self, instance, data):
        print 'save form data:', (instance, data)
        setattr(instance, self.name, data)

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        from baph.db.models.base import Model as Base

        defaults = {'required': self.required,
                    'label': capfirst(self.verbose_name),
                    'help_text': self.help_text}
        if self.has_default():
            if callable(self.default):
                defaults['initial'] = self.default
                defaults['show_hidden_initial'] = True
            else:
                defaults['initial'] = self.get_default()

        if self.collection_class is not None:
            defaults['collection_class'] = self.collection_class
            if issubclass(self.data_type, Base):
                defaults['related_class'] = self.data_type
            form_class = fields.MultiObjectField

        if form_class is None and self.data_type in FIELD_MAP:
            form_class = FIELD_MAP[self.data_type]
        #return self.formfield(field_cls, **kwargs)
        '''
        if self.data_collection in COLLECTION_MAP:
            type_ = COLLECTION_MAP[self.data_collection]
        elif self.uselist:
            type_ = types.List
        elif issubclass(self.data_type, Base):
            type_ = object
        else:
            type_ = self.data_type
        '''
        # TODO: convert the 'choices' logic?
        ''' 
        if self.choices:
            include_blank = (self.blank or
                             not (self.has_default() or 'initial' in kwargs))
            defaults['choices'] = self.get_choices(include_blank=include_blank)
            defaults['coerce'] = self.to_python
            if self.null:
                defaults['empty_value'] = None
            if choices_form_class is not None:
                form_class = choices_form_class
            else:
                form_class = forms.TypedChoiceField
            # Many of the subclass-specific formfield arguments (min_value,
            # max_value) don't apply for choice fields, so be sure to only pass
            # the values that TypedChoiceField will understand.
            for k in list(kwargs):
                if k not in ('coerce', 'empty_value', 'choices', 'required',
                             'widget', 'label', 'initial', 'help_text',
                             'error_messages', 'show_hidden_initial'):
                    del kwargs[k]
        '''
        defaults.update(kwargs)
        if form_class is None:
            form_class = fields.NullCharField
        #print form_class, defaults
        return form_class(**defaults)

    def clean(self, value, model_instance):
        print 'clean:', (self, value, model_instance)
        return self.formfield().clean(value)

    @classmethod
    def field_from_attr(cls, key, attr, model):
        kwargs = cls.field_kwargs_from_attr(key, attr, model)
        return cls(**kwargs)

    @classmethod
    def field_kwargs_from_attr(cls, key, attr, model):
        #print (cls, key, attr, model)
        #info = dict((k, getattr(attr, k, None)) for k in dir(attr))
        if attr.extension_type == ASSOCIATION_PROXY:
            kwargs = cls.field_kwargs_from_proxy(key, attr, model)
        elif isinstance(attr.property, ColumnProperty):
            kwargs = cls.field_kwargs_from_column(key, attr, model)
        elif isinstance(attr.property, RelationshipProperty):
            kwargs = cls.field_kwargs_from_relationship(key, attr, model)
        else:
            raise Exception('field_kwargs_from_attr can only be called on'
                             'proxies, columns, and relationships')
        kwargs['attname'] = key
        return kwargs

    @classmethod
    def field_kwargs_from_column(cls, key, attr, model):
        kwargs = {'name': attr.key}
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
            kwargs['editable'] = not kwargs['auto'] and not attr.info.get('readonly', False)
            if type(col.type) == Boolean:
                kwargs['required'] = False
            elif not col.nullable and not kwargs['auto'] and not kwargs['default']: 
                kwargs['required'] = True
            else:
                kwargs['required'] = False
            if hasattr(col.type, 'length'):
                kwargs['max_length'] = col.type.length

        else:
            # multiple join elements, make it readonly
            kwargs['editable'] = False

        return kwargs

    @classmethod
    def field_kwargs_from_relationship(cls, key, attr, model):
        kwargs = {'name': attr.key}
        prop = attr.property
        data_type = get_related_class_from_attr(attr)
        collection_class = prop.collection_class
        collection_class = normalize_collection_class(collection_class)
        if not collection_class and prop.uselist:
            collection_class = list

        kwargs['data_type'] = data_type
        kwargs['uselist'] = prop.uselist
        kwargs['editable'] = not prop.viewonly
        kwargs['nullable'] = True
        if collection_class:
            kwargs['collection_class'] = [collection_class]
        return kwargs

    @classmethod
    def field_kwargs_from_proxy(cls, key, attr, model):
        proxy = getattr(model, key)
        #info = (attr.target_class, attr.value_attr)
        kwargs = cls.field_kwargs_from_attr(key, attr.remote_attr, model)

        collection_class = attr.local_attr.property.collection_class
        collection_class = normalize_collection_class(collection_class)
        if not collection_class and attr.local_attr.property.uselist:
            collection_class = list

        collections = kwargs.get('collection_class', [])
        if collection_class:
            collections.insert(0, collection_class)
        kwargs['collection_class'] = collections
        kwargs['name'] = key
        kwargs['proxy'] = True
        kwargs['nullable'] = True
        return kwargs

    def value_from_object(self, instance):
        from baph.db.orm import ORM
        orm = ORM.get()
        Base = orm.Base
        value = getattr(instance, self.name, None)
        #if isinstance(value, Base):
        #    cls, args = identity_key(instance=value)
        #    value = ','.join(str(arg) for arg in args)
        return value
