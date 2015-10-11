from optparse import make_option
from importlib import import_module
import inspect as inspect_
import types

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError
from django.utils.datastructures import SortedDict
from sqlalchemy import *
from sqlalchemy import inspect
from sqlalchemy import interfaces
from sqlalchemy.ext.associationproxy import *
from sqlalchemy.ext.declarative import declarative_base, clsregistry
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import *
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.mapper import configure_mappers
from sqlalchemy.util import duck_type_collection

from baph.apps import apps
from baph.core.management.base import BaseCommand
from baph.db.models.utils import class_resolver, process_proxy, process_rel


ALLOWED_MODES = ('registry', 'model', 'modelmeta', 'modelfields', 'form')

class Command(BaseCommand):
    help = ("Get debugging info")
    requires_system_checks = False
    
    def add_arguments(self, parser):
        parser.add_argument('mode', metavar='mode', nargs=1, help='debug type')
        parser.add_argument('values', metavar='values', nargs='*', help='values')        
    
    def handle(self, **options):
        mode = options['mode'][0]
        if mode not in ALLOWED_MODES:
            raise CommandError('Invalid mode "%s". Allowed modes are %s'
                % (mode, ', '.join(ALLOWED_MODES)))

        if mode == 'registry':
            print 'The registry contains the following apps:'
            for config in apps.get_app_configs():
                print config.label
                for model in config.models.values():
                    print '  ', model

        if mode == 'model':
            model_name = options['values'][0]
            model = apps.get_model(model_name)
            mapper = inspect(model)

            for attr_name in dir(model):
                try:    
                    attr = getattr(model, attr_name)
                    if isinstance(attr, AssociationProxy):
                        attr.key = attr_name
                except: 
                    pass

            max_key_len = max(len(attr.key) for attr in mapper.all_orm_descriptors
                if not attr.is_mapper)
            print model, 'has the following attributes:'

            # columns first
            print '[COLUMNS]'
            for prop in mapper.column_attrs:
                print '  ', prop.key.ljust(max_key_len+2), repr(prop.columns[0])

            # now relationships
            print '[RELATIONSHIPS]'
            for prop in mapper.relationships:
                info = process_rel(prop)
                print '  ', prop.key.ljust(max_key_len+2), info['data_type'], \
                    info['collection_class']

            # now associationproxies
            print '[ASSOCIATION PROXIES]'
            for attr in mapper.all_orm_descriptors:
                if attr.is_mapper:
                    continue
                elif attr.extension_type == ASSOCIATION_PROXY:
                    info = process_proxy(attr)
                    print '  ', attr.key.ljust(max_key_len+2), repr(info['data_type']), \
                        info['collection_class']
            
        if mode == 'modelmeta':
            model_name = options['values'][0]
            model = apps.get_model(model_name)
            max_key_len = max(len(key) for key in dir(model._meta))
            print '%s has the following metadata:' % model_name
            for key in dir(model._meta):
                if key[0] == '_':
                    continue
                value = getattr(model._meta, key)
                if inspect_.ismethod(value):
                    continue
                print '  ', key.ljust(max_key_len+2), value

        if mode == 'modelfields':
            model_name = options['values'][0]
            model = apps.get_model(model_name)
            max_key_len = max(len(field.name) for field in model._meta.fields)
            print '%s has the following model fields:' % model_name
            for field in model._meta.fields:
                print '  ', field.name.ljust(max_key_len+2), repr(field)

        if mode == 'form':
            form_class = options['values'][0]
            module_name, form_name = form_class.rsplit('.', 1)
            module = import_module(module_name)
            form = getattr(module, form_name)
            print '%s has the following base_fields:' % form
            for field_name, field in form.base_fields.items():
                print '  ', field_name, field
            '''
            model = apps.get_model(model_name)
            max_key_len = max(len(field.name) for field in model._meta.fields)
            print '%s has the following model fields:' % model_name
            for field in model._meta.fields:
                print '  ', field.name.ljust(max_key_len+2), repr(field)
            '''