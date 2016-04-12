from baph.db.utils import DEFAULT_DB_ALIAS


class DatabaseRouter(object):
    def db_for_read(self, model, **hints):
        return DEFAULT_DB_ALIAS

    def db_for_write(self, model, **hints):
        return DEFAULT_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        return False

    def allow_migrate(self, db, model):
        return False

'''
class Base(object):
    id = Column(Integer, primary_key=True)
    data = Column(String(50))
    def __repr__(self):
        return "%s(id=%r, data=%r)" % (
            self.__class__.__name__,
            self.id, self.data
        )

Base = declarative_base(cls=Base)

class DefaultBase(Base):
    __abstract__ = True
    metadata = MetaData()

class OtherBase(Base):
    __abstract__ = True
    metadata = MetaData()

class Model1(DefaultBase):
    __tablename__ = 'model1'

class Model2(DefaultBase):
    __tablename__ = 'model2'

class Model3(OtherBase):
    __tablename__ = 'model3'

class RoutingSession(Session):

    def get_bind(self, mapper=None, clause=None):
        if mapper and issubclass(mapper.class_, Base):
            return engines['other']
        elif self._flushing:
            return engines['leader']
        else:
            return engines[random.choice(['follower1', 'follower2'])]

Session = scoped_session(sessionmaker(class_=RoutingSession, autocommit=True))

for eng in 'leader', 'follower1', 'follower2':
    DefaultBase.metadata.create_all(engines[eng])
OtherBase.metadata.create_all(engines['other'])
'''