import operator
import time
from collections import defaultdict
from functools import partial
from urllib import unquote

from cached_property import cached_property
from django.core.cache.backends.memcached import MemcachedCache


KEY_VALUE_SPLITTER = operator.methodcaller('split', '=', 1)


def parse_metadump(line):
    # line format: <key>=<value>*
    # split = operator.methodcaller('split', '=', 1)
    pairs = [(key, unquote(value).encode('utf8'))
             for key, value in map(KEY_VALUE_SPLITTER, line)]
    return dict(pairs)


def parse_cachedump(line, **kwargs):
    data = dict(kwargs)
    key, metadata = line
    data['key'] = key.encode('utf8')
    metadata = metadata[1:-1]  # strip brackets
    for key in ('size', 'exp'):
        stat, sep, metadata = metadata.partition(';')
        value, unit = stat.strip().split(' ', 1)
        data[key] = int(value)
    return data


def parse_stat(line):
    # line format: STAT <key> <value>
    return (line[1], line[2])


class MemcacheServer(object):
    def __init__(self, server):
        self.server = server

    @property
    def settings(self):
        return dict(self.get_stats('settings'))

    @property
    def slabs(self):
        return self.get_slabs()

    def send_command(self, cmd, row_len=0, expect=None):
        """
        send a command to the server, and returns a parsed response

        the response is a list of lines
        each line in the list is a list of space-delimited strings
        """
        if not self.server.connect():
            return
        self.server.send_cmd(cmd)
        if expect:
            self.server.expect(expect)
            return None
        lines = []
        while True:
            line = self.server.readline()
            if not line:
                break
            line = line.decode('ascii').strip()
            while line:
                # readline splits on '\r\n', we still need to split on '\n'
                item, sep, line = line.partition('\n')
                if item == 'END':
                    return lines
                else:
                    lines.append(item.split(' ', row_len-1))
        return lines

    # command implementations

    def flush_all(self):
        """
        flushes all keys in the cache

        returns None
        """
        cmd = 'flush_all'
        return self.send_command(cmd, expect='OK')

    def get_metadump(self, slab_id):
        """
        Returns a list of (key, value) tuples containing cache item stats
        """
        cmd = 'lru_crawler metadump %s' % slab_id
        return map(parse_metadump, self.send_command(cmd))

    def get_stats(self, *args):
        """
        returns a list of (key, value) tuples for a stats command
        """
        cmd = ' '.join(('stats',) + args)
        return map(parse_stat, self.send_command(cmd, 3))

    # STATS command variants

    def get_slabs(self):
        """
        gets configuration settings for active slabs
        """
        slabs = defaultdict(dict)
        for key, value in self.get_stats('items'):
            # key format: items:<slab_id>:<key>
            _, slab_id, key = key.split(':', 2)
            slabs[slab_id][key] = value
        return slabs

    def get_slab_stats(self):
        """
        gets statistics for active slabs
        """
        slab_stats = defaultdict(dict)
        for key, value in self.get_stats('slabs'):
            # key format 1: <slab_id>:<key>
            # key format 2: <total_key>
            if ':' in key:
                slab_id, key = key.split(':')
            else:
                slab_id = 'totals'
            slab_stats[slab_id][key] = value
        return slab_stats

    def get_cachedump(self, slab_id, limit):
        limit = limit or 0
        cmd = 'cachedump %s %s' % (slab_id, limit)
        return map(parse_cachedump, self.get_stats(cmd))

    def get_slab_keys_from_metadump(self, slab_id, limit=None):
        """
        returns all keys in a slab using 'lru_crawler metadump'
        """
        # metadump doesn't support a limit param, so we need to handle it
        items = self.get_metadump(slab_id)
        return items[:limit]

    def get_slab_keys_from_cachedump(self, slab_id, limit=None):
        """
        returns all keys in a slab using 'stats cachedump'
        """
        return self.get_cachedump(slab_id, limit)

    def get_slab_keys(self, slab_id, limit=None):
        """
        returns all keys in a slab, as a list of dicts
        """
        if self.settings.get('lru_crawler', 'no') == 'yes':
            return self.get_slab_keys_from_metadump(slab_id, limit)
        else:
            return self.get_slab_keys_from_cachedump(slab_id, limit)

    def get_keys_from_metadump(self, limit=None):
        """
        returns all keys on the server using 'lru_crawler metadump'
        """
        return self.get_slab_keys_from_metadump('all', limit)

    def get_keys_from_cachedump(self, limit=None):
        """
        returns all keys on the server using 'stats cachedump'
        """
        func = partial(self.get_slab_keys_from_cachedump, limit=limit)
        return reduce(operator.concat, map(func, self.slabs), [])

    def get_keys(self, limit=None, include_expired=False):
        """
        returns all keys on the server, as a list of strings
        """
        if self.settings.get('lru_crawler', 'no') == 'yes':
            func = self.get_keys_from_metadump
        else:
            func = self.get_keys_from_cachedump

        getter = operator.itemgetter('key')
        ts = int(time.time())
        items = func(limit)
        if not include_expired:
            # expiration of 0 means an item never expires
            items = filter(lambda x: x['exp'] == 0 or x['exp'] > ts, items)
        return map(getter, items)


class BaphMemcachedCache(MemcachedCache):
    """
    An extension of the django memcached Cache class
    """
    def __init__(self, server, params):
        super(BaphMemcachedCache, self).__init__(server, params)
        self.version = params.get('VERSION', 0)
        self.alias = params.get('ALIAS', None)

    def __str__(self):
        return '<BaphMemcachedCache: alias=%r>' % self.alias

    @property
    def ident(self):
        return '(%s:%s)' % (self.alias, id(self))

    @cached_property
    def servers(self):
        return map(MemcacheServer, self._cache.servers)

    def get_all_keys(self):
        """
        Returns all keys on all servers

        Keys may or may not be valid - a flush_all command does not
        have any impact on the keys, and invalidation is handled later
        by comparing a value in the server settings to the 'time' attribute
        of the cached item (that attribute is not retrievable, so there is
        no way to get the 'real' list of keys
        """
        keys = set()
        for server in self.servers:
            keys.update(server.get_keys())
        return keys

    def flush_all(self):
        """
        Invalidates all keys on all servers
        """
        for server in self.servers:
            server.flush_all()

    def get_raw(self, key):
        """
        does a cache lookup for a key, without running it through the
        make_key function
        """
        return self._cache.get(key)

    def dump(self):
        """
        Dumps the contents of the cache as a dict
        """
        data = {}
        for key in self.get_all_keys():
            value = self.get_raw(key)
            if value is not None:
                data[key] = value
        return data
