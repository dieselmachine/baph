

class BaseOptions(object):
  propagate = ()
  defaults = {}

  def __init__(self, options):
    self.options = options
    for name in self.defaults:
      setattr(self, name, self.defaults[name])

  def contribute_to_class(self, cls, name):
    base_options = getattr(cls, name, None)
    setattr(cls, name, self)
    self.model = cls
    
    # Store the original user-defined values for each option,
    # for use when serializing the model definition
    self.original_attrs = {}
    self.inherited_attrs = {}

    if self.options:
      options = self.options.__dict__.copy()
      for name in self.options.__dict__:
        # ignore private attributes
        if name.startswith('_'):
          del options[name]
      for name in self.defaults.iterkeys():
        if name in options:
          setattr(self, name, options.pop(name))
          self.original_attrs[name] = getattr(self, name)
        elif hasattr(self.options, name):
          setattr(self, name, getattr(self.options, name))
          self.original_attrs[name] = getattr(self, name)

      # any leftover attributes are invalid
      if options != {}:
        raise TypeError("'class %s' got invalid attribute(s): %s"
          % (None, ','.join(options.keys())))

    if base_options:
      # copy inheritable values from parent if not provided
      for name in self.propagate:
        if not hasattr(self.options, name):
          setattr(self, name, getattr(base_options, name))
          self.inherited_attrs[name] = getattr(self, name)

    del self.options