from collections import defaultdict

from django.core.cache import get_cache
from django.utils.functional import cached_property
from django.utils.termcolors import make_style

from sqlalchemy import *
from sqlalchemy.orm import class_mapper

from baph.core.management.new_base import BaseCommand
from baph.db.orm import ORM


success_msg = make_style(fg='green')
notice_msg = make_style(fg='yellow')
error_msg = make_style(fg='red')
info_msg = make_style(fg='blue')

orm = ORM.get()
Base = orm.Base


def prompt_for_model_name(cacheable_models):
    while True:
        cmd = raw_input('\nKill cache for which model? '
                        '(ENTER to list, Q to quit): ')
        if cmd in ('q', 'Q'):
            return None
        if not cmd.strip():
            for name in sorted(cacheable_models):
                print '    %s' % name
            continue
        return cmd

def prompt_for_pk(model):
    print 'Enter the primary key components:'
    pk = []
    for col in class_mapper(model).primary_key:
        v = raw_input('    %s: ' % col.name)
        pk.append(v)
    return tuple(pk)

class Command(BaseCommand):
    requires_model_validation = True
    help = "Kills cache keys for baph models"
    args = "modelname [id id ...]"

    def add_arguments(self, parser):
        parser.add_argument('model_name', nargs='?',
            help='The name of the model')
        parser.add_argument('model_pks', nargs='*',
            help='The primary keys to invalidate')

    @cached_property
    def cacheable_models(self):
        models = {}
        for name, model in Base._decl_class_registry.items():
            if hasattr(model, '_meta') and model._meta.cache_detail_fields:
                models[name] = model
        return models

    def handle(self, **options):
        print 'handle:', options
        model_name = options['model_name']
        pks = options['model_pks']

        print ''
        while True:
            if not model_name:
                model_name = prompt_for_model_name(self.cacheable_models)
            if not model_name:
                # quit
                break
            #if not model_name in Base._decl_class_registry:
            if not model_name in self.cacheable_models:
                print error_msg('Invalid model name: %s' % model_name)
                model_name = None
                continue
            model = self.cacheable_models[model_name]

            if not pks:
                pk = prompt_for_pk(model)
                pks = [pk]
            
            session = orm.sessionmaker()
            for pk in pks:
                print info_msg('\nLooking up %r with pk=%s' % (model_name, pk))
                obj = session.query(model).get(pk)
                if not obj:
                    print error_msg('  No %s found with PK %s' % (model_name, pk))
                    continue

                print success_msg('  Found object: %r' % obj)

                caches = defaultdict(lambda: {
                    'cache_keys': set(),
                    'version_keys': set(),
                })
                cache_keys, version_keys = obj.get_cache_keys(
                    child_updated=True, force_expire_pointers=True)

                if cache_keys:
                    for alias, cache_key in cache_keys:
                        caches[alias]['cache_keys'].add(cache_key)

                if version_keys:
                    for alias, version_key in version_keys:
                        caches[alias]['version_keys'].add(version_key)

                for alias, keys in caches.items():
                    print info_msg('Processing keys on cache %r' % alias)
                    cache = get_cache(alias)
                    for key in keys['cache_keys']:
                        print '  Killing cache key: %r' % key
                    cache.delete_many(keys['cache_keys'])
                    for key in keys['version_keys']:
                        print '  Incrementing version key: %r' % key
                        if cache.get(key):
                            cache.incr(key)

            model_name = None
            pks = None
