from __future__ import unicode_literals

from flask import Flask


def setup():
  print 'setup'
  from baph.apps import apps
  from baph.conf import settings

  apps.populate(settings.INSTALLED_APPS)

def create_app(*args, **kwargs):
  print 'create_app'
  from baph.conf import settings

  setup()
  app = Flask(__name__)
  app.config.from_object(settings)
  print 'returning:', app
  return app