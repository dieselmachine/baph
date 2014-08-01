"""
Wrapper for loading templates from "templates" directories in INSTALLED_APPS
packages.
"""

import os
import sys

from baph.apps import apps
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader
from django.utils._os import safe_join
from django.utils import six

from coffin.template.loader import get_template
from jinja2.loaders import FileSystemLoader


def calculate_app_template_dirs():
    if six.PY2:
        fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
    app_template_dirs = []
    for app_config in apps.get_app_configs():
        if not app_config.path:
            continue
        template_dir = os.path.join(app_config.path, 'templates')
        if os.path.isdir(template_dir):
            if six.PY2:
                template_dir = template_dir.decode(fs_encoding)
            app_template_dirs.append(template_dir)
    return tuple(app_template_dirs)


# At compile time, cache the directories to search.
app_template_dirs = calculate_app_template_dirs()


class Loader(FileSystemLoader):
    is_usable = True

    def __init__(self, *args, **kwargs):
        super(Loader, self).__init__(app_template_dirs)

    def __call__(self, template_name, template_dirs=None):
        return self.load_template(template_name, template_dirs)

    def load_template(self, template_name, template_dirs=None):
        extension = os.path.splitext(template_name)[1]
        template = get_template(template_name)
        return template, template.filename

    def load_template_source(self, template_name, template_dirs=None):
        tried = []
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                with open(filepath, 'rb') as fp:
                    return (fp.read().decode(settings.FILE_CHARSET), filepath)
            except IOError:
                tried.append(filepath)
        if tried:
            error_msg = "Tried %s" % tried
        else:
            error_msg = "Your TEMPLATE_DIRS setting is empty. Change it to point to at least one template directory."
        raise TemplateDoesNotExist(error_msg)
    load_template_source.is_usable = True

