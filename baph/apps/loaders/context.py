from importlib import import_module

from django.utils.module_loading import module_has_submodule


class BaseLoader(object):
    def load_app(self, app):
        pass


class ContextLoader(BaseLoader):
    @classmethod
    def load_app(cls, app):
        if module_has_submodule(app.module, 'globals'):
            module_name = '%s.%s' % (app.name, 'globals')
            import_module(module_name)
