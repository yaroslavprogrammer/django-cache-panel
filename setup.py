#!/usr/bin/env python

from setuptools import setup, find_packages

VERSION = __import__('cache_panel').__version__

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name='django-cache-panel',
    version=VERSION,
    description='A more detailed cache panel for the Django Debug Toolbar',
    long_description=long_description,
    author='Brandon Konkle',
    author_email='brandon@lincolnloop.com',
    url='http://github.com/lincolnloop/django-cache-panel',
    packages=find_packages(),
    provides=['cache_panel'],
    requires=['Django', 'debug_toolbar'],
    include_package_data=True,
    zip_safe=False,
)
