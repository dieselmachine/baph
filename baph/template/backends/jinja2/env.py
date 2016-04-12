import os

from django.template.context import _builtin_context_processors
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import gettext, ngettext
import jinja2
from jinja2._compat import encode_filename

from baph.template.backends.jinja2.parser import Parser


def supermakedirs(path, mode):
    if not path or os.path.exists(path):
        return []
    (head, tail) = os.path.split(path)
    res = supermakedirs(head, mode)
    os.mkdir(path)
    os.chmod(path, mode)
    res += [path]
    return res

class Environment(jinja2.Environment):
    def __init__(self, *args, **kwargs):
        self.context_processors = kwargs.pop('context_processors', [])
        filters = kwargs.pop('filters', {})
        super(Environment, self).__init__(*args, **kwargs)

        # create the bytecode cache directory if needed
        cache = self.bytecode_cache
        if cache and hasattr(cache, 'directory'):
            if cache.directory and not os.path.exists(cache.directory):
                try:
                    os.makedirs(cache.directory)
                except:
                    # permission denied! delete the bytecode cache setting
                    raise
                    self.bytecode_cache = None

        # set up gettext callables for translations
        self.install_gettext_callables(gettext, ngettext)
        
        # install the manually defined filters
        for name, path in filters.items():
            self.filters[name] = import_string(path)
        
        # install the default django filters
        from django.template.defaultfilters import register
        for name in register.filters:
            if name not in self.filters:
                # only install if they don't overwrite existing filters
                self.filters[name] = register.filters[name]

    def _parse(self, source, name, filename):
        """Internal parsing function used by `parse` and `compile`."""
        return Parser(self, source, name, encode_filename(filename)).parse()

    @cached_property
    def template_context_processors(self):
        context_processors = _builtin_context_processors
        context_processors += tuple(self.context_processors)
        return tuple(import_string(path) for path in context_processors)
