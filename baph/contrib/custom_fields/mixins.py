#from baph.db.models.base import Model
from baph.db.models.fields import Field

from .models import CustomField


#orm = ORM.get()

class ExtendableModelMixin(object):
    """ mixin to add custom fields to classes """
    pass
    """
    @classmethod
    def get_custom_fields(cls, owner_id):
        if not cls._meta.extension_field:
            raise Exception('extension_field must be defined')
        session = orm.sessionmaker()
        custom_fields = session.query(CustomField) \
            .filter(CustomField.owner_id==owner_id) \
            .filter(CustomField.model==cls._meta.object_name) \
            .all()
        for field in custom_fields:
            yield field.as_modelfield()
    """