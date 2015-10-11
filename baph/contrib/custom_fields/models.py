from sqlalchemy import *

from baph.db.models.fields import Field
from baph.db.models.base import Model as Base


data_types = {
	'integer': Integer,
	'text': Unicode,
	'decimal': Float,
	'boolean': Boolean,
	}

class CustomField(Base):
    __tablename__ = 'custom_fields'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False)
    model = Column(String, nullable=False)
    name = Column(Unicode, nullable=False)
    slug = Column(String, nullable=False)
    description = Column(Unicode)
    type = Column(String) # int / text / boolean / decimal
    required = Column(Boolean, default=False)
    encrypted = Column(Boolean, default=False)

    def as_modelfield(self):
    	return Field(name=self.name, help_text=self.description,
    		data_type=data_types[self.type], required=self.required)