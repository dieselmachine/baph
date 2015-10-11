from django.db import connections
from django.db.models import manager
from sqlalchemy.orm import query


def ensure_default_manager(cls):
    """
    Ensures that a Model subclass contains a default manager  and sets the
    _default_manager attribute on the class. Also sets up the _base_manager
    points to a plain Manager instance (which could be the same as
    _default_manager if it's not a subclass of Manager).
    """
    if cls._meta.swapped:
        setattr(cls, 'objects', manager.SwappedManagerDescriptor(cls))
        return
    if not getattr(cls, '_default_manager', None):
        if hasattr(cls, 'objects'):
            raise ValueError(
                "Model %s must specify a custom Manager, because it has a "
                "field named 'objects'" % cls.__name__
            )
        # Create the default manager, if needed.
        cls.add_to_class('objects', Manager())
        cls._base_manager = cls.objects
    elif not getattr(cls, '_base_manager', None):
        default_mgr = cls._default_manager.__class__
        if (default_mgr is Manager or
                getattr(default_mgr, "use_for_related_fields", False)):
            cls._base_manager = cls._default_manager
        else:
            # Default manager isn't a plain Manager class, or a suitable
            # replacement, so we walk up the base class hierarchy until we hit
            # something appropriate.
            for base_class in default_mgr.mro()[1:]:
                if (base_class is Manager or
                        getattr(base_class, "use_for_related_fields", False)):
                    cls.add_to_class('_base_manager', base_class())
                    return
            raise AssertionError(
                "Should never get here. Please report a bug, including your "
                "model and model manager setup."
            )

class Query(query.Query):

    def __init__(self, entities, session=None, query=None, using=None, hints=None):
        if hints:
            print 'ignoring hints:', hints
        if query:
            print 'ignoring query:', query

        if using:
            session = connections[alias].session()
        return super(Query, self).__init__(entities, session)

    def using(self, alias):
        self.session = connections[alias or 'default'].session()
        return self

class Manager(manager.BaseManager.from_queryset(Query)):

    def get_queryset(self):
        print 'get queryset'
        session = connections[self.db or 'default'].session()
        return self._queryset_class(self.model, session=session)