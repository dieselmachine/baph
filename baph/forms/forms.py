from collections import OrderedDict

from django import forms
from django.db.models.fields import Field as ModelField
from django.forms.fields import Field
from django.forms.widgets import MediaDefiningClass
from django.utils.translation import ugettext_lazy as _
from sqlalchemy import *
from sqlalchemy.orm.attributes import instance_dict
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.util import has_identity, identity_key
from sqlalchemy.sql.expression import _BinaryExpression, _Label

from baph.db import types, ORM


orm = ORM.get()

def save_instance(form, instance, fields=None, fail_message='saved',
                  commit=True, exclude=None):
    """
    Saves bound Form ``form``'s cleaned_data into model instance ``instance``.

    If commit=True, then the changes to ``instance`` will be saved to the
    database. Returns ``instance``.
    """
    opts = instance._meta
    for k,v in form.cleaned_data.items():
        if k in form.data:
            try:
                # TODO: this fails when trying to reach the remote side
                # of an association_proxy when the interim node is None
                # find a better solution
                setattr(instance, k, v)
            except TypeError as e:
                continue
                
    if form.errors:
        raise ValueError("The %s could not be %s because the data didn't"
                         " validate." % (opts.object_name, fail_message))


class DeclarativeFieldsMetaclass(MediaDefiningClass):
    """
    Metaclass that collects Fields declared on the base classes.
    """
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        print 'declarative fields metaclass', name, attrs
        current_fields = []
        for key, value in list(attrs.items()):
            print '  field: %s' % key
            if isinstance(value, (Field, ModelField)):
                print '    found declared field: "%s"' % key
                current_fields.append((key, value))
                attrs.pop(key)
        current_fields.sort(key=lambda x: x[1].creation_counter)
        attrs['declared_fields'] = OrderedDict(current_fields)

        new_class = (super(DeclarativeFieldsMetaclass, mcs)
            .__new__(mcs, name, bases, attrs))

        # Walk through the MRO.
        declared_fields = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, 'declared_fields'):
                declared_fields.update(base.declared_fields)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_fields:
                    declared_fields.pop(attr)

        new_class.base_fields = declared_fields
        new_class.declared_fields = declared_fields

        return new_class