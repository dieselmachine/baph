from django.core.validators import EMPTY_VALUES
from django.forms.widgets import TextInput, DateInput, DateTimeInput, TimeInput, Select, SelectMultiple
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.util import identity_key


class HTML5EmailInput(TextInput):
    input_type = 'email'

class HTML5NumberInput(TextInput):
    input_type = 'number'

class HTML5DateInput(DateInput):
    input_type = 'date'

class HTML5DateTimeInput(DateTimeInput):
    input_type = 'datetime'

class HTML5TimeInput(TimeInput):
    input_type = 'time'

class ObjectSelect(Select):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        super(ObjectSelect, self).__init__(*args, **kwargs)

    def value_from_datadict(self, data, files, name):
        value = super(ObjectSelect, self).value_from_datadict(data, files, name)
        if value in EMPTY_VALUES:
            return None
        session = orm.sessionmaker()
        obj = session.query(self.model).get(value.split(','))
        return obj

class MultiObjectSelect(SelectMultiple):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model')
        #assert False
        attrs = kwargs.pop('attrs', {})
        attrs['class'] = 'chosen-select'
        kwargs['attrs'] = attrs
        super(MultiObjectSelect, self).__init__(*args, **kwargs)

    def value_from_datadict(self, data, files, name):
        pk = class_mapper(self.model).primary_key
        if len(pk) > 1:
            assert False
        value = data.getlist(name, [])
        col = getattr(self.model, pk[0].name)

        session = orm.sessionmaker()
        objs = session.query(self.model) \
            .filter(col.in_(value)) \
            .all()
        return objs

