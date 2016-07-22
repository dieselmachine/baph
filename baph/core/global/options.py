from baph.core.options.base import BaseOptions


class GlobalizeOptions(BaseOptions):
  defaults = {
    # column is the name of the boolean column which indicates
    # global status. This must be set in order to use globalization
    'column': None,
    # parents is a list of relationships which should be checked
    # on object creation, and if a global parent is found, the new
    # object will be globalized
    'parents': [],
    # cascades is a list of relationships through which 
    # globalization should propagate (all children become globals)
    'cascades': [],
  }

  def globalize(self, instance, commit=True):
    """
    Converts object into a global by creating an instance of 
    Meta.global_class with the same identity key.
    """
    from baph.db.orm import ORM
    orm = ORM.get()

    if not self.column:
      raise Exception('You cannot globalize a class with no value '
                      'for Global.column')

    # TODO: delete polymorphic extension, leave only the base

    setattr(instance, self.column, True)

    # handle meta.global_cascades
    for field in self.cascades:
      value = getattr(instance, field, None)
      if not value:
        continue
      if isinstance(value, orm.Base):
        # single object
        value.globalize(commit=False)
      elif hasattr(value, 'iteritems'):
        # dict-like collection
        for obj in value.values():
          obj.globalize(commit=False)
      elif hasattr(value, '__iter__'):
        # list-like collection
        for obj in value:
          obj.globalize(commit=False)
   
    if commit:
      session = orm.sessionmaker()
      session.add(self)
      session.commit()

  def is_globalized(self, instance):
    return getattr(instance, self.column)
