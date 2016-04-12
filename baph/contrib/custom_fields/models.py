from django.db.models import fields
from sqlalchemy import *

from baph.db.models.fields import Field
from baph.db.models.base import Model as Base


data_types = {
	'integer': fields.IntegerField,
	'text': fields.CharField,
	'decimal': fields.DecimalField,
	'boolean': fields.BooleanField,
	}

class CustomField(Base):
    __tablename__ = 'custom_fields'

    class Meta:
        list_actions = ['add']
        detail_actions = [
            'view',
            'edit',
            'delete',
            ]

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False)
    model = Column(String, nullable=False)
    name = Column(Unicode, nullable=False)
    slug = Column(String, nullable=False)
    description = Column(Unicode)
    type = Column(String) # int / text / boolean / decimal
    required = Column(Boolean, default=False)
    encrypted = Column(Boolean, default=False)

    def as_modelfield(self, cls):
        field_class = data_types[self.type]
        field_kwargs = {
            'help_text': self.description,
            'name': self.slug,
            'verbose_name': self.name,
            'blank': not self.required,
            'null': not self.required,
            }
        if self.type == 'text':
            field_kwargs['max_length'] = 255
        field = field_class(**field_kwargs)
        field.contribute_to_class(cls, self.slug)
        return field