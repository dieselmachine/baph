from collections import OrderedDict
import warnings

from django import forms
from django.core.exceptions import (NON_FIELD_ERRORS, FieldError, 
    ImproperlyConfigured, ValidationError)
from django.db.models import fields as modelfields
from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.models import construct_instance, model_to_dict, fields_for_model
from django.forms.utils import ErrorList
from django.utils import six
from sqlalchemy import *
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.orm.attributes import instance_dict
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.sql.expression import _BinaryExpression, _Label

from baph.db import types
from baph.db.models.base import Model as Base
from baph.forms import fields
from baph.forms.widgets import ObjectSelect, MultiObjectSelect


ALL_FIELDS = '__all__'
'''
def construct_instance(form, instance, fields=None, exclude=None):
    """
    Constructs and returns a model instance from the bound ``form``'s
    ``cleaned_data``, but does not save the returned instance to the
    database.
    """
    #print 'construct instance:'
    #print 'fields:', fields
    #print 'exclude:', exclude
    #print form.data
    from django.db import models
    opts = instance._meta

    cleaned_data = form.cleaned_data
    #print 'cleaned data:', cleaned_data
    file_field_list = []
    for f in opts.fields:
        if not f.editable or isinstance(f, models.AutoField) \
                or f.name not in cleaned_data:
            #print '    ignoring non-editable/non-submitted field "%s"' % f.name
            continue
        if fields is not None and f.name not in fields:
            #print '    ignoring field not present in `fields`: "%s"' % f.name
            continue
        if exclude and f.name in exclude:
            #print '    ignoring exluded field "%s"' % f.name
            continue
        # Defer saving file-type fields until after the other fields, so a
        # callable upload_to can use the values from other fields.
        #print '    including field %s' % f.name
        if isinstance(f, models.FileField):
            file_field_list.append(f)
        else:
            f.save_form_data(instance, cleaned_data[f.name])

    for f in file_field_list:
        f.save_form_data(instance, cleaned_data[f.name])

    return instance
'''
'''
def model_to_dict(instance, fields=None, exclude=None):
    opts = instance._meta
    data = instance_dict(instance).copy()
    for f in opts.fields:
        if not getattr(f, 'editable', False):
            continue
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)

    return data
'''
'''
def fields_for_model(model, fields=None, exclude=None, widgets=None, 
                     formfield_callback=None, localized_fields=None,
                     labels=None, help_texts=None, error_messages=None,
                     field_classes=None):

    field_list = []
    ignored = []
    opts = model._meta


    # pull labels from the model, then update with local values
    form_labels = opts.labels or {}
    if labels:
        form_labels.update(labels)

    # pull help text from the model, then update with local values
    form_help_texts = opts.help_texts or {}
    if help_texts:
        form_help_texts.update(help_texts)

    #print '\nfields for model:', model
    for f in sorted(opts.fields):
        if not getattr(f, 'editable', False):
            #print '  skipping non-editable field "%s"' % f.name
            continue
        if fields is not None and not f.name in fields:
            #print '  skipping non-included field "%s"' % f.name
            continue
        if exclude and f.name in exclude:
            #print '  skipping excluded field "%s"' % f.name
            continue

        kwargs = {}
        if widgets and f.name in widgets:
            kwargs['widget'] = widgets[f.name]
        if localized_fields == ALL_FIELDS or (localized_fields 
                                and f.name in localized_fields):
            kwargs['localize'] = True
        if form_labels and f.name in form_labels:
            kwargs['label'] = form_labels[f.name]
        if form_help_texts and f.name in form_help_texts:
            kwargs['help_text'] = form_help_texts[f.name]
        if error_messages and f.name in error_messages:
            kwargs['error_messages'] = error_messages[f.name]
        if field_classes and f.name in field_classes:
            kwargs['form_class'] = field_classes[f.name]
        
        if formfield_callback is None:
            formfield = f.formfield(**kwargs)
        elif not callable(formfield_callback):
            raise TypeError('formfield_callback must be a function or callable')
        else:
            formfield = formfield_callback(f, **kwargs)

        if formfield:
            #print '  adding field "%s"' % f.name
            field_list.append((f.name, formfield))
        else:
            ignored.append(f.name)

    field_dict = OrderedDict(field_list)
    if fields:
        field_dict = OrderedDict(
            [(f, field_dict.get(f)) for f in fields
                if ((not exclude) or (exclude and f not in exclude)) 
                and (f not in ignored)]
        )
    return field_dict
'''
class ModelFormOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)
        self.widgets = getattr(options, 'widgets', None)
        self.localized_fields = getattr(options, 'localized_fields', None)
        self.labels = getattr(options, 'labels', None)
        self.help_texts = getattr(options, 'help_texts', None)
        self.error_messages = getattr(options, 'error_messages', None)
        self.field_classes = getattr(options, 'field_classes', None)
        self.exclude_on_create = getattr(options, 'exclude_on_create', [])
        self.exclude_on_update = getattr(options, 'exclude_on_update', [])
        self.exclude_on_nested = getattr(options, 'exclude_on_nested', [])

class ModelFormMetaclass(DeclarativeFieldsMetaclass):
    def __new__(cls, name, bases, attrs):
        formfield_callback = attrs.pop('formfield_callback', None)

        new_class = super(ModelFormMetaclass, cls) \
            .__new__(cls, name, bases, attrs)

        if bases == (BaseModelForm,):
            return new_class

        opts = new_class._meta = ModelFormOptions(getattr(new_class, 'Meta', None))
        
        if opts.model:
            # If a model is defined, extract form fields from it.
            if opts.fields is None and opts.exclude is None:
                # This should be some kind of assertion error once deprecation
                # cycle is complete.
                warnings.warn("Creating a ModelForm without either the 'fields' attribute "
                              "or the 'exclude' attribute is deprecated - form %s "
                              "needs updating" % name,
                              DeprecationWarning, stacklevel=2)

            if opts.fields == ALL_FIELDS:
                # sentinel for fields_for_model to indicate "get the list of
                # fields from the model"
                opts.fields = None

            fields = fields_for_model(opts.model, opts.fields, opts.exclude,
                                      opts.widgets, formfield_callback,
                                      opts.localized_fields, opts.labels,
                                      opts.help_texts, opts.error_messages)

            # make sure opts.fields doesn't specify an invalid field
            none_model_fields = [k for k, v in six.iteritems(fields) if not v]
            missing_fields = (set(none_model_fields) -
                             set(new_class.declared_fields.keys()))
            if missing_fields:
                message = 'Unknown field(s) (%s) specified for %s'
                message = message % (', '.join(missing_fields),
                                     opts.model.__name__)
                raise FieldError(message)
            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(new_class.declared_fields)
        else:
            fields = new_class.declared_fields

        new_class.base_fields = fields

        return new_class


class BaseModelForm(BaseForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                  initial=None, error_class=ErrorList, label_suffix=None,
                  empty_permitted=False, instance=None, nested=False,
                  extension_owner=None):
        opts = self._meta
        if opts.model is None:
            raise ValueError('ModelForm has no model class specified')
        if instance is None:
            self.instance = opts.model()
            object_data = {}
        else:
            self.instance = instance
            object_data = model_to_dict(instance, opts.fields, opts.exclude)
        if initial is not None:
            object_data.update(initial)

        self._validate_unique = False
        self.nested = nested
        super(BaseModelForm, self).__init__(data, files, auto_id, prefix,
                                             object_data, error_class,
                                             label_suffix, empty_permitted)
        
        custom_fields = self.get_custom_fields(extension_owner)
        for field in custom_fields:
            self.fields[field.name] = field.formfield()

        # Apply ``limit_choices_to`` to each field.
        for field_name in self.fields:
            formfield = self.fields[field_name]
            if hasattr(formfield, 'queryset') and hasattr(formfield,
                       'get_limit_choices_to'):
                limit_choices_to = formfield.get_limit_choices_to()
                if limit_choices_to is not None:
                    formfield.queryset = formfield.queryset \
                             .complex_filter(limit_choices_to)

    def get_custom_fields(self, owner):
        model = self._meta.model
        return model.get_custom_fields(owner)

    def _get_validation_exclusions(self):
        """
        For backwards-compatibility, several types of fields need to be
        excluded from model validation. See the following tickets for
        details: #12507, #12521, #12553
        """
        print 'get validation exclusion:'
        exclude = []
        # Build up a list of fields that should be excluded from model field
        # validation and unique checks.
        for f in self.instance._meta.fields:
            field = f.name
            # Exclude fields that aren't on the form. The developer may be
            # adding these values to the model after form validation.
            if field not in self.fields:
                print '    excluding field not in fields: "%s"' % field
                exclude.append(f.name)

            # Don't perform model validation on fields that were defined
            # manually on the form and excluded via the ModelForm's Meta
            # class. See #12901.
            elif self._meta.fields and field not in self._meta.fields:
                print '    excluding field in exclude "%s"' % field
                exclude.append(f.name)
            elif self._meta.exclude and field in self._meta.exclude:
                print '    excluding field in form.exclude: "%s"' % field
                exclude.append(f.name)

            # Exclude fields that failed form validation. There's no need for
            # the model fields to validate them as well.
            elif field in self._errors.keys():
                print '    excluding field due to validation failure: %s' % field
                exclude.append(f.name)

            # Exclude empty fields that are not required by the form, if the
            # underlying model field is required. This keeps the model field
            # from raising a required error. Note: don't exclude the field from
            # validation if the model field allows blanks. If it does, the blank
            # value may be included in a unique check, so cannot be excluded
            # from validation.
            else:
                form_field = self.fields[field]
                field_value = self.cleaned_data.get(field)
                if not f.blank and not form_field.required \
                        and field_value in form_field.empty_values:
                    print '    excluding non-required empty field: %s' % field
                    exclude.append(f.name)
        return exclude

    def clean(self):
        print 'form.clean'
        self._validate_unique = True
        return self.cleaned_data

    def _update_errors(self, errors):
        # Override any validation error messages defined at the model level
        # with those defined at the form level.
        opts = self._meta

        # Allow the model generated by construct_instance() to raise
        # ValidationError and have them handled in the same way as others.
        if hasattr(errors, 'error_dict'):
            error_dict = errors.error_dict
        else:
            error_dict = {NON_FIELD_ERRORS: errors}

        for field, messages in error_dict.items():
            if (field == NON_FIELD_ERRORS and opts.error_messages and
                    NON_FIELD_ERRORS in opts.error_messages):
                error_messages = opts.error_messages[NON_FIELD_ERRORS]
            elif field in self.fields:
                error_messages = self.fields[field].error_messages
            else:
                continue

            for message in messages:
                if (isinstance(message, ValidationError) and
                        message.code in error_messages):
                    message.message = error_messages[message.code]

        self.add_error(None, errors)

    def _post_clean(self):
        print '_post_clean'
        opts = self._meta

        exclude = self._get_validation_exclusions()

        try:
            self.instance = construct_instance(self, self.instance,
                                               opts.fields, exclude)
        except ValidationError as e:
            self._update_errors(e)
        print self.instance.to_dict()
        try:
            self.instance.full_clean(exclude=exclude, validate_unique=False)
        except ValidationError as e:
            self._update_errors(e)

        # Validate uniqueness if needed.
        #if self._validate_unique:
        #    self.validate_unique()


    def save(self, commit=True):

        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )
        if commit:
            self.instance.save()
        return self.instance

    save.alters_data = True


class ModelForm(BaseModelForm):
    __metaclass__ = ModelFormMetaclass
