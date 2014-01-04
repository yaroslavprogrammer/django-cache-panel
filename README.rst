==================
Django Cache Panel
==================

.. image:: https://raw.github.com/lincolnloop/django-cache-panel/master/screenshot.png

The Django Cache Panel is an add-on for the Django Debug Toolbar to track cache
usage. It is a fork of the `Cache Debug Toolbar <https://github.com/WoLpH/Cache-Debug-Toolbar>`_
project by Rick van Hattem, which is where the statistics tracking at the core
of this project comes from. The generic cache wrapper is modified from the
`django-debug-cache-panel <https://github.com/jbalogh/django-debug-cache-panel>`_
project by Jeff Balogh.

It's been tested with Django 1.4 and Django Debug Toolbar 0.9.4 using the
python-memcached backend. If you've tried it out with other configurations,
please let me know!

What's Changed?
===============

The project has been modified to be more generic, capturing only the functions
found in the BaseCache so that it should be compatible with more cache
backends. The way the statistics are captured and the presentation of the
statistics has also been modified to be more similar to the SQL panel. The
requirement for the panel to be imported in settings has been removed.

Installation
============

#. Install and configure `Django Debug Toolbar <https://github.com/django-debug-toolbar/django-debug-toolbar>`_.
#. ``pip install django-cache-panel``
#. Add ``cache_panel`` app to your ``INSTALLED_APPS``.
#. Add ``cache_panel.panel.CacheDebugPanel`` to ``DEBUG_TOOLBAR_PANELS``.
