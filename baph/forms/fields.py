import json

from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.util import identity_key

from django import forms
from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _


BOOLEAN_CHOICES = [
    (None, 'All'),
    (True, 'True'),
    (False, 'False'),
    ]
    
class NullBooleanChoiceField(forms.ChoiceField):
    """
    Choice field with None, True, and False as choices
    """
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = BOOLEAN_CHOICES
        super(NullBooleanChoiceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        v2 = super(NullBooleanChoiceField, self).to_python(value)
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        return None

class NullCharField(forms.CharField):
    """
    CharField that does not cast None to ''
    """
    def to_python(self, value):
        "Returns a Unicode object."
        if value in validators.EMPTY_VALUES:
            return None
        return super(NullCharField, self).to_python(value)

class MultiObjectField(forms.MultipleChoiceField):
    """
    Field for handling of collections of objects
    """
    def __init__(self, related_class=None, collection_class=None, **kwargs):
        print 'MOF.__init__', related_class, collection_class
        self.related_class = related_class
        self.collection_class = collection_class
        super(MultiObjectField, self).__init__(**kwargs)

    def validate_collection(self, data, collection_class=None):
        print 'MOF.validate_collection'
        if collection_class is None:
            collection_class = self.collection_class[:]
        if collection_class == []:
            # we've drilled down through all collections, now we
            # check the class type if available
            if self.related_class and not isinstance(data, self.related_class):
                raise forms.ValidationError(
                    _('Expected %s, got %s') % (self.related_class, type(data)))
            return
        c_cls = collection_class.pop(0)
        if c_cls == dict:
            if not isinstance(data, dict):
                raise forms.ValidationError(
                    _('Expected dict, got %s') % type(data))
            for k,v in data.items():
                self.validate_collection(v, collection_class)
        elif c_cls == list:
            if not isinstance(data, list):
                raise forms.ValidationError(
                    _('Expected list, got %s') % type(data))
            for v in data:
                self.validate_collection(v, collection_class)

    def prepare_value(self, value):
        print 'MOF.prepare_value', (value,)
        results = []
        for item in value or []:
            if hasattr(item, '_meta'):
                cls, args = identity_key(instance=item)
                item = ','.join(str(arg) for arg in args)
            results.append(item)
        return results
        return super(MultiObjectField, self).prepare_value(value)

    def to_python(self, value):
        print 'MOF.to_python', (value, self.related_class)
        print self.widget
        from baph.db.orm import Base
        if value in validators.EMPTY_VALUES:
            print 'empty values'
            return []
        print self.collection_class, self.related_class, value
        self.validate_collection(value)
        return value

        pk = class_mapper(self.related_class).primary_key
        if len(pk) > 1:
            assert False
        #value = data.getlist(name, None)
        col = getattr(self.related_class, pk[0].name)
        assert False

        session = orm.sessionmaker()
        objs = session.query(self.model) \
            .filter(col.in_(value)) \
            .all()
        return objs


        return value        

    def valid_value(self, value):
        print 'MOF.valid_value', value
        "Check to see if the provided value is a valid choice"
        cls, args = identity_key(instance=value)
        text_value = ','.join(str(arg) for arg in args)
        return super(MultiObjectField, self).valid_value(text_value)


class ObjectField(forms.ChoiceField):
    " allowed values must be sqlalchemy objects (result of resource hydration)"
    def __init__(self, related_class=None, **kwargs):
        if not related_class:
            raise ImproperlyConfigured(u'No related class assigned to '
                                            'ObjectField')
        self.related_class = related_class
        super(ObjectField, self).__init__(**kwargs)

    def prepare_value(self, value):
        if hasattr(value, '_meta'):
            cls, args = identity_key(instance=value)
            return ','.join(str(arg) for arg in args)
        return super(ObjectField, self).prepare_value(value)

    def to_python(self, value):
        from baph.db.orm import ORM, Base
        orm = ORM.get()
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, self.related_class):
            return value
        if isinstance(value, Base):
            raise forms.ValidationError(
                _('This field expects an object of class %s'
                   % type(self.related_class)))
        # assume what we have is a stringified primary key
        session = orm.sessionmaker()
        args = value.split(',')
        value = session.query(self.related_class).get(args)
        if not value:
            raise forms.ValidationError(
                _('The specified object does not exist'))
        return value

    def valid_value(self, value):
        "Check to see if the provided value is a valid choice"
        cls, args = identity_key(instance=value)
        text_value = ','.join(str(arg) for arg in args)
        return super(ObjectField, self).valid_value(text_value)
        

class JsonField(forms.Field):

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, basestring):
            try:
                value = json.loads(value)
            except:
                raise forms.ValidationError(_('JSON could not be deserialized'))
        return value

class ListField(JsonField):
    " allowed values must be in list form "
    def to_python(self, value):
        if value is None:
            return value
        if value in validators.EMPTY_VALUES:
            return []
        value = super(ListField, self).to_python(value)
        # sqlalchemy.ext.associationproxy._AssociationList (and similar) does 
        # not subclass list, so we check for __iter__ to determine validity
        if not hasattr(value, '__iter__') or hasattr(value, 'items'):
            raise forms.ValidationError(_('This field requires a list as input'))
        return value

class DictField(JsonField):
    " allowed values must be in dict form "
    def to_python(self, value):
        if value is None:
            return value
        if value in validators.EMPTY_VALUES:
            return {}
        value = super(DictField, self).to_python(value)
        # sqlalchemy.ext.associationproxy._AssociationDict does not subclass
        # dict, so we check for .items to determine validity
        if not hasattr(value, 'items'): 
            raise forms.ValidationError(_('This field requires a dict as input'))
        return value

# TODO: Test these
"""
class OneToManyField(ListField):
    " input from an html form will be a list of primary keys "
    " input from resource hydration will be the objects themselves "
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        super(OneToManyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        value = super(OneToManyField, self).to_python(value)
        if all(isinstance(v, int) for v in value):
            # list of primary keys
            session = orm.sessionmaker()
            return session.query(self.model) \
                .filter(self.model.id.in_(value)) \
                .all()
        elif all(isinstance(v, self.model) for v in value):
            # list of instances
            return value
        raise ValueError(_('This field takes a list of pks or instances of %s' \
            % self.model))

class ManyToManyField(ListField):
    " input from an html form will be a list of primary keys "
    " input from resource hydration will be the objects themselves "
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        super(ManyToManyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        value = super(ManyToManyField, self).to_python(value)
        if all(isinstance(v, int) for v in value):
            # list of primary keys
            session = orm.sessionmaker()
            return session.query(self.model) \
                .filter(self.model.id.in_(value)) \
                .all()
        elif all(isinstance(v, self.model) for v in value):
            # list of instances
            return value
        raise ValueError(_('This field takes a list of pks or instances of %s' \
            % self.model))
"""
