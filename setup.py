#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from distutils.core import setup
from setuptools import find_packages

setup(name='baph',
      version='0.3.4',
      install_requires=[
          'Django >= 1.8.19',
          'django-jinja == 2.4.1',
          'funcy',
          'SQLAlchemy >= 0.9.0',
          'python-dotenv == 0.7.1',
          'functools32 == 3.2.3.post2; python_version < "3.0"',
      ],
      include_package_data=True,
      package_data={
          '': ['*.rst'],
      },
      packages=find_packages(),
      zip_safe=False)
