from __future__ import absolute_import
from contextlib import contextmanager

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

from baph.db import DEFAULT_DB_ALIAS