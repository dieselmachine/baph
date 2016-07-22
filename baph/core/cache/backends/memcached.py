"Memcached cache backend"

import pickle
import time

import six

from baph.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache
from baph.utils.encoding import force_str
from baph.utils.functional import cached_property


class BaseMemcachedCache(BaseCache):
    def __init__(self, server, params, library, value_not_found_exception):
        super(BaseMemcachedCache, self).__init__(params)
        if isinstance(server, six.string_types):
            self._servers = server.split(';')
        else:
            self._servers = server

        # The exception type to catch from the underlying library for a key
        # that was not found. This is a ValueError for python-memcache,
        # pylibmc.NotFound for pylibmc, and cmemcache will return None without
        # raising an exception.
        self.LibraryValueNotFoundException = value_not_found_exception

        self._lib = library
        self._options = params.get('OPTIONS')

    @property
    def _cache(self):
        """
        Implements transparent thread-safe access to a memcached client.
        """
        if getattr(self, '_client', None) is None:
            self._client = self._lib.Client(self._servers)

        return self._client

    def get_backend_timeout(self, timeout=DEFAULT_TIMEOUT):
        """
        Memcached deals with long (> 30 days) timeouts in a special
        way. Call this function to obtain a safe value for your timeout.
        """
        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout

        if timeout is None:
            # Using 0 in memcache sets a non-expiring timeout.
            return 0
        elif int(timeout) == 0:
            # Other cache backends treat 0 as set-and-expire. To achieve this
            # in memcache backends, a negative timeout must be passed.
            timeout = -1

        if timeout > 2592000:  # 60*60*24*30, 30 days
            # See https://github.com/memcached/memcached/wiki/Programming#expiration
            # "Expiration times can be set from 0, meaning "never expire", to
            # 30 days. Any time higher than 30 days is interpreted as a Unix
            # timestamp date. If you want to expire an object on January 1st of
            # next year, this is how you do that."
            #
            # This means that we have to switch to absolute timestamps.
            timeout += int(time.time())
        return int(timeout)

    def make_key(self, key, version=None):
        # Python 2 memcache requires the key to be a byte string.
        return force_str(super(BaseMemcachedCache, self).make_key(key, version))

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        return self._cache.add(key, value, self.get_backend_timeout(timeout))

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        val = self._cache.get(key)
        if val is None:
            return default
        return val

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        if not self._cache.set(key, value, self.get_backend_timeout(timeout)):
            # make sure the key doesn't keep its old value in case of failure to set (memcached's 1MB limit)
            self._cache.delete(key)

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self._cache.delete(key)

    def get_many(self, keys, version=None):
        new_keys = [self.make_key(x, version=version) for x in keys]
        ret = self._cache.get_multi(new_keys)
        if ret:
            _ = {}
            m = dict(zip(new_keys, keys))
            for k, v in ret.items():
                _[m[k]] = v
            ret = _
        return ret

    def close(self, **kwargs):
        self._cache.disconnect_all()

    def incr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)
        # memcached doesn't support a negative delta
        if delta < 0:
            return self._cache.decr(key, -delta)
        try:
            val = self._cache.incr(key, delta)

        # python-memcache responds to incr on non-existent keys by
        # raising a ValueError, pylibmc by raising a pylibmc.NotFound
        # and Cmemcache returns None. In all cases,
        # we should raise a ValueError though.
        except self.LibraryValueNotFoundException:
            val = None
        if val is None:
            raise ValueError("Key '%s' not found" % key)
        return val

    def decr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)
        # memcached doesn't support a negative delta
        if delta < 0:
            return self._cache.incr(key, -delta)
        try:
            val = self._cache.decr(key, delta)

        # python-memcache responds to incr on non-existent keys by
        # raising a ValueError, pylibmc by raising a pylibmc.NotFound
        # and Cmemcache returns None. In all cases,
        # we should raise a ValueError though.
        except self.LibraryValueNotFoundException:
            val = None
        if val is None:
            raise ValueError("Key '%s' not found" % key)
        return val

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        safe_data = {}
        for key, value in data.items():
            key = self.make_key(key, version=version)
            safe_data[key] = value
        self._cache.set_multi(safe_data, self.get_backend_timeout(timeout))

    def delete_many(self, keys, version=None):
        self._cache.delete_multi(self.make_key(key, version=version) for key in keys)

    def clear(self):
        self._cache.flush_all()

    # baph extensions

    def delete_many_raw(self, keys):
        """
        Deletes the specified keys (does not run them through make_key)
        """
        self._cache.delete_multi(keys)

    def flush_all(self):
        for s in self._cache.servers:
            if not s.connect(): continue
            s.send_cmd('flush_all')
            s.expect("OK")
            self.delete_many_raw(self.get_server_keys(s))

    def get_all_keys(self):
        keys = set()
        for s in self._cache.servers:
            keys.update(self.get_server_keys(s))
        return keys

    def get_server_keys(self, s):
        keys = set()
        slab_ids = self.get_server_slab_ids(s)
        for slab_id in slab_ids:
            keys.update(self.get_slab_keys(s, slab_id))
        return keys

    def get_slab_keys(self, s, slab_id):
        keys = set()
        s.send_cmd('stats cachedump %s 100' % slab_id)
        readline = s.readline
        ts = time.time()
        while 1:
            line = readline()
            if not line or line.strip() == 'END': break
            frags = line.split(' ')
            key = frags[1]
            expire = int(frags[4])
            if expire > ts:
                keys.add(key)
        return keys

    def get_server_slab_ids(self, s):
        if not s.connect():
            return set()
        slab_ids = set()
        s.send_cmd('stats items')
        readline = s.readline
        while 1:
            line = readline()
            if not line or line.strip() == 'END': break
            frags = line.split(':')
            slab_ids.add(frags[1])
        return slab_ids

class MemcachedCache(BaseMemcachedCache):
    "An implementation of a cache binding using python-memcached"
    def __init__(self, server, params):
        import memcache
        super(MemcachedCache, self).__init__(server, params,
                                             library=memcache,
                                             value_not_found_exception=ValueError)

    @property
    def _cache(self):
        if getattr(self, '_client', None) is None:
            self._client = self._lib.Client(self._servers, pickleProtocol=pickle.HIGHEST_PROTOCOL)
        return self._client


class PyLibMCCache(BaseMemcachedCache):
    "An implementation of a cache binding using pylibmc"
    def __init__(self, server, params):
        import pylibmc
        super(PyLibMCCache, self).__init__(server, params,
                                           library=pylibmc,
                                           value_not_found_exception=pylibmc.NotFound)

    @cached_property
    def _cache(self):
        client = self._lib.Client(self._servers)
        if self._options:
            client.behaviors = self._options

        return client
