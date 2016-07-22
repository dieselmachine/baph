from baph.core.cache import DEFAULT_CACHE_ALIAS
from baph.core.options.base import BaseOptions


class CacheOptions(BaseOptions):
  defaults = {
    'alias': DEFAULT_CACHE_ALIAS,
    'timeout': None,
    'detail_fields': [],
    'list_fields': [],
    # cache_pointers is a list of identity keys which contain no data
    # other than the primary key of the object being pointed at.
    # format: (cache_key_template, columns, name)
    # cache_key_template and columns function as above, and 'name' is
    # an alias to help distinguish between keys during unittesting
    # when an update occurs, two actions occur: the new value is set
    # to the current object, and the previous value (if different) is
    # set to False (not deleted)
    'pointers': [],
    # cache_relations is a list of relations which should be monitored
    # for changes when generating cache keys for invalidation. This should
    # be used for relationships to composite keys, which cannot be
    # handled properly via cache_cascades
    'relations': [],
    # cache_cascades is a list of relations through which to cascade
    # invalidations. Use this when an object is cached as a subobject of
    # a larger cache, to signal the parent that it needs to recache
    'cascades': [],
  }

  def get_cache(self):
    """
    Returns the cache associated with this model, based on the value
    of meta.cache_alias
    """
    return get_cache(self.alias)

  def get_cache_namespaces(self, instance=None):
    """
    Returns the cache namespaces for the class
    """
    return []

  @property
  def cache_namespaces(self):
    return self.get_cache_namespaces()

  def build_cache_key(self, mode, **kwargs):
    """
    Generates a cache key for the provided mode and the given kwargs
    mode is one of ['list', 'detail', or 'list_version']
    if mode is detail, cache_detail_fields must be defined
    if mode is list or list_version, cache_list_fields must be defined
    The associated fields must all be present in kwargs
    """
    if mode not in ('detail', 'list', 'list_version'):
      raise Exception('Invalid mode "%s" for build_cache_key. '
        'Valid modes are "detail", "list", and "list_version"')

    _mode = 'list' if mode == 'list_version' else mode
    fields = getattr(self, 'cache_%s_fields' % _mode)
    if not fields:
      raise Exception('cache_%s_fields is not defined' % _mode)

    cache = self.get_cache()

    cache_pieces = []
    cache_pieces.append(self.model._meta.base_model_name_plural)
    cache_pieces.append(_mode)

    for key in sorted(fields):
      # all associated fields must be present in kwargs
      if not key in kwargs:
        raise Exception('%s is undefined' % key)
      cache_pieces.append('%s=%s' % (key, kwargs.pop(key)))

    version_key = ':'.join(cache_pieces)

    if mode == 'list_version':
      return version_key

    ns_pieces = []
    for key, value in sorted(self.get_cache_namespaces()):
      ns_key = '%s_%s' % (key, value)
      version = cache.get(ns_key)
      if version is None:
        version = int(time.time())
        cache.set(ns_key, version)
      ns_pieces.append('%s_%s' % (ns_key, version))

    if mode == 'detail':
      cache_key = ':'.join(ns_pieces + cache_pieces)
      return cache_key

    # treat list keys as version keys, so we can invalidate
    # multiple subsets (filters, pagination, etc) at once
    version = cache.get(version_key)
    if version is None:
      version = int(time.time())
      cache.set(version_key, version)
    cache_key = '%s_%s' % (version_key, version)

    filters = []
    for key, value in sorted(kwargs.items()):
      filters.append('%s=%s' % (key, value))

    cache_key = ':'.join(ns_pieces + [cache_key] + filters)
    return cache_key

  @property
  def cache_key(self):
      """
      Instance property which returns the cache key for a single object
      """
      if not has_identity(self):
          raise Exception('This instance has no identity')
      if not hasattr(self._meta, 'cache_detail_fields'):
          raise Exception('Meta.cache_detail_fields is undefined')
      data = dict((k, getattr(self, k)) for k in self._meta.cache_detail_fields)
      return self.build_cache_key('detail', **data)

  @property
  def cache_list_version_key(self):
      """
      Instance property which returns the cache list version key for a single object
      """
      if not hasattr(self._meta, 'cache_list_fields'):
          raise Exception('Meta.cache_list_fields is undefined')
      data = dict((k, getattr(self, k)) for k in self._meta.cache_list_fields)
      return self.build_cache_key('list_version', **data)

  @property
  def cache_list_key(self):
      """
      Instance property which returns the cache list key for a single object
      """
      if not hasattr(self._meta, 'cache_list_fields'):
          raise Exception('Meta.cache_list_fields is undefined')
      data = dict((k, getattr(self, k)) for k in self._meta.cache_list_fields)
      return self.build_cache_key('list', **data)

  def cache_pointers(self, data=None, columns=[]):
      if not hasattr(self._meta, 'cache_pointers'):
          return {}
      data = data or instance_dict(self)
      keys = {}
      for raw_key, attrs, name in self._meta.cache_pointers:
          if columns and not any(c in attrs for c in columns):
              continue
          keys[name] = raw_key % data
      return keys

  @property
  def cache_pointer_keys(self):
      if not hasattr(self._meta, 'cache_pointers'):
          raise Exception('Meta.cache_pointers is undefined')
      return self.cache_pointers()

  def get_cache_keys(self, child_updated=False, force_expire_pointers=False):
      cache_keys = set()
      version_keys = set()

      orm = ORM.get()
      session = orm.sessionmaker()
      deleted = self.is_deleted or self in session.deleted
      data = instance_dict(self)
      cache = self.get_cache()

      # get a list of all fields which changed
      changed_keys = []
      for attr in self.__mapper__.iterate_properties:
        if not isinstance(attr, ColumnProperty) and \
            attr.key not in self._meta.cache_relations:
          continue
        if attr.key in IGNORABLE_KEYS:
          continue
        ins, eq, rm = get_history(self, attr.key)
        if ins or rm:
          changed_keys.append(attr.key)
      self_updated = bool(changed_keys) or deleted

      if not self_updated and not child_updated:
        return (cache_keys, version_keys)

      if self._meta.cache_detail_fields:
        if has_identity(self):
          # we only kill primary cache keys if the object exists
          # this key won't exist during CREATE
          cache_key = self.cache_key
          cache_keys.add(cache_key)

      if self._meta.cache_list_fields:
        # collections will be altered by any action, so we always
        # kill these keys
        cache_key = self.cache_list_version_key
        version_keys.add(cache_key)

      # pointer records contain only the id of the parent resource
      # if changed, we set the old key to False, and set the new key
      pointers = []
      for raw_key, attrs, name in self._meta.cache_pointers:
          if attrs and not any(key in changed_keys for key in attrs) \
                   and not force_expire_pointers:
              # the fields which trigger this key were not changed
              continue
          cache_key = raw_key % data
          c, idkey = identity_key(instance=self)
          if len(idkey) > 1:
              idkey = ','.join(str(i) for i in idkey)
          else:
              idkey = idkey[0]
          if not self.is_deleted:
              cache.set(cache_key, idkey)
          if force_expire_pointers:
              cache_keys.add(cache_key)

          # if this is an existing object, we need to handle the old key
          if not has_identity(self):
              continue

          old_data = {}
          for attr in attrs:
              ins,eq,rm = get_history(self, attr)
              old_data[attr] = rm[0] if rm else eq[0]
          old_key = raw_key % old_data
          if old_key == cache_key and not self.is_deleted:
              continue
          old_idkey = cache.get(old_key)
          if old_idkey == idkey:
              # this object is the current owner of the key
              cache.set(old_key, False)

      # cascade the cache kill operation to related objects, so parents
      # know if children have changed, in order to rebuild the cache
      for cascade in self.cascades:
          objs = getattr(self, cascade)
          if not objs:
            continue
          if not isinstance(objs, list):
            objs = [objs]
          for obj in objs:
            k1, k2 = obj.get_cache_keys(child_updated=True)
            cache_keys.update(k1)
            version_keys.update(k2)

      return (cache_keys, version_keys)

  def kill_cache(self, force=False):
      cache_logger.debug('kill_cache called for %s' % self)
      cache_keys, version_keys = self.get_cache_keys(child_updated=force)
      if not cache_keys and not version_keys:
          cache_logger.debug('%s has no cache keys' % self)
          return

      cache_logger.debug('%s has the following cache keys:' % self)
      for key in cache_keys:
          cache_logger.debug('\t%s' % key)
      cache_logger.debug('%s has the following version keys:' % self)
      for key in version_keys:
          cache_logger.debug('\t%s' % key)

      cache = self.get_cache()
      cache.delete_many(cache_keys)
      for key in version_keys:
        v = cache.get(key)
        if not v:
          cache.set(key, int(time.time()))
        else:
          cache.incr(key)
