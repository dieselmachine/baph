from baph.core.options.base import BaseOptions


class PermissionOptions(BaseOptions):
  defaults = {
    'permissions': [],
    'scopes': [],
    'list_actions': [],
    'detail_actions': [],
    'classes': [],
    # permission_parents is a list of *toOne relations which can be
    # considered to refer to 'parents'. These relations will automatically
    # be considered when generating possible permission paths
    'parents': [],
    'full_parents': [],
    # permission_handler is the name of the parent relation through which
    # to route permission requests for this object
    'handler': [],
    # permission_limiters is a dict, with each key containing an 'alias'
    # for the limiter, used in generating codenames. Each value is a dict,
    # with the key referring to the local column to be checked, and the
    # value containing an expression which will be evaluated against the
    # permission's context
    'limiters': [],
    'terminator': None,
    # permission_resources is a dict, with each key containing a resource
    # name to expose (generally the lowercased classname), and a value 
    # containing a list of actions available on that resource
    # ex: { 'image': ['add', 'edit', 'delete', 'view', 'crop'] }
    'resources': [],
  }

  def get_context(self, depth=0):
    ctx = {}
    for key, attr in inspect(self.model).all_orm_descriptors.items():
      if not attr.is_attribute:
        continue
      if type(attr.property) == ColumnProperty:
        cls_name = self.model.__name__.lower()
        ctx_key = '%s.%s' % (cls_name, key)
        continue
      if type(attr.property) != RelationshipProperty:
        continue
      if attr.property.direction.name != 'MANYTOONE':
        continue
      if len(attr.property.local_remote_pairs) != 1:
        continue
      parent = getattr(self, key)
      if parent and depth == 0:
        ctx.update(parent.get_context(depth=1))
    return ctx

  @classmethod
  def get_fks(cls, include_parents=True, remote_key=None):
    keys = []
    cls_name = cls.__name__

    if len(cls.__mapper__.primary_key) == 1:
      primary_key = cls.__mapper__.primary_key[0].key
    else:
      primary_key = None

    # add permission for unrestricted access
    keys.append( ('any', None, None, None, cls_name) )

    # add permission for single instance access (single-col pk only)
    if primary_key:
      col_key = '%s_%s' % (cls._meta.model_name, primary_key)
      value = '%%(%s)s' % col_key
      keys.append( ('single', primary_key, value, col_key, cls_name) )

    # iterate through limiters and create a list of local permissions
    for limiter, pairs in cls._meta.permission_limiters.items():
      col_key = None
      new_key = remote_key or primary_key
      if new_key in pairs:
        value = pairs[new_key]
      else:
        primary_key, value = pairs.items()[0]
      keys.append( (limiter, primary_key, value, col_key, cls_name) )

    if not include_parents:
      return keys

    # using this node as a base, grab the keys from parent objects
    # and create expressions to grant child access via parents
    fks = []
    for key in cls._meta.permission_parents + cls._meta.permission_full_parents:
      # 'key' is the name of the parent relation attribute
      attr = getattr(cls, key)
      if not attr.is_attribute:
        continue
      prop = attr.property
      if type(prop) != RelationshipProperty:
        continue
      if prop.direction.name != 'MANYTOONE':
        continue
      if len(prop.local_remote_pairs) != 1:
        continue

      sub_cls = cls.get_related_class(key)
      col = prop.local_remote_pairs[0][0]
      col_attr = column_to_attr(cls, col)
      remote_col = prop.local_remote_pairs[0][1]

      inc_par = sub_cls._meta.permission_terminator == False or \
                key in cls._meta.permission_full_parents
      sub_fks = sub_cls.get_fks(include_parents=inc_par,
                                remote_key=remote_col.key)

      for limiter, key_, value, col_key, base_cls in sub_fks:
        if not key_:
          # do not extend the 'any' permission
          continue

        # prepend the current node string to each filter in the 
        # limiter expression
        frags = key_.split(',')
        frags = ['%s.%s' % (key, frag) for frag in frags]
        key_ = ','.join(frags)

        frags = value.split(',')
        if len(frags) > 1:
          frags = [f for f in frags if f.find('.') == -1]
          if len(frags) == 1:
            new_col_key = frags[0][2:-2]

        if limiter == 'single' or not col_key:
          col_key = col_attr.key
          attr = getattr(cls, col_attr.key, None)
          if not isinstance(attr, RelationshipProperty):
            # the column is named differently from the attr
            for k,v in cls.__mapper__.all_orm_descriptors.items():
              if not hasattr(v, 'property'):
                continue
              if not isinstance(v.property, ColumnProperty):
                continue
              if v.property.columns[0] == col:
                col_key = k
                break

        if limiter == 'single':
          # for single limiters, we can eliminate the final join
          # and just use the value of the fk instead
          limiter = key_.split('.')[-2]
          value = '%%(%s)s' % col_key

        keys.append( (limiter, key_, value, col_key, cls_name) )
    return keys

  @classmethod
  def get_related_class(cls, rel_name):
    attr = getattr(cls, rel_name)
    prop = attr.property
    related_cls = prop.argument
    if isinstance(related_cls, types.FunctionType):
      # lazy-loaded Model
      related_cls = related_cls()
    if isinstance(related_cls, _class_resolver):
      # lazy-loaded Model
      related_cls = related_cls()
    if hasattr(related_cls, 'is_mapper') and related_cls.is_mapper:
      # we found a mapper, grab the class from it
      related_cls = related_cls.class_
    return related_cls

  def get_parent(self, attr_name):
    # first, try grabbing it directly
    parent = getattr(self, attr_name)
    if parent:
      return parent
        
    # if nothing was found, grab the fk and lookup manually
    mapper = inspect(type(self))
    attr = getattr(type(self), attr_name)
    prop = attr.property
    local_col, remote_col = prop.local_remote_pairs[0]
    local_prop = mapper.get_property_by_column(local_col)
    value = getattr(self, local_prop.key)

    if not value:
      # no relation and no fk = no parent
      return None

    parent_cls = type(self).get_related_class(attr_name)
    mapper = inspect(parent_cls)
    remote_prop = mapper.get_property_by_column(remote_col)
    filters = {remote_prop.key: value}

    orm = ORM.get()
    session = orm.sessionmaker()
    parent = session.query(parent_cls).filter_by(**filters).first()
    return parent

  @classmethod
  def normalize_key(cls, key):
    limiter = ''
    frags = key.split('.')
    if len(frags) > 1:
      # expression contains multiple relations
      col_name = frags.pop()
      rel_name = frags.pop()

      current_cls = base_cls = cls
      for f in frags:
        current_cls = current_cls.get_related_class(f)
      prev_cls = current_cls
      current_rel = getattr(current_cls, rel_name)
      current_cls = current_cls.get_related_class(rel_name)

      col = getattr(current_cls, col_name)

      attr = None
      for loc, rem in current_rel.property.local_remote_pairs:
        if rem in col.property.columns:
          attr = loc.name
          for c in inspect(prev_cls).all_orm_descriptors:
            try:
              cols = c.property.columns
              assert len(cols) == 1
              if cols[0] == loc:
                attr = c.key
                break
            except:
              pass
          break
      if attr:
        if frags:
          limiter = ' ' + ' '.join(reversed(frags))
        frags.append(attr)
        key = '.'.join(frags)
      else:
        frags.append(rel_name)
        limiter = ' ' + ' '.join(reversed(frags))

    return (key, limiter)