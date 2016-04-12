from sqlalchemy import *
from sqlalchemy.dialects.postgresql import JSON

from baph.contrib.auth.models import User
from baph.db.models.base import Base


class UserViewConfig(Base):
    __tablename__ = 'user_view_configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    view_name = Column('model', String, nullable=False)
    fields = Column(JSON, nullable=False)

