#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

from kiwi_rebuild_plugin.version import __version__


config = {
    'name': 'kiwi_rebuild_plugin',
    'description': 'KIWI - Rebuild Images Plugin',
    'author': 'David Cassany',
    'url': 'https://github.com/OSInside/kiwi-rebuild-plugin',
    'download_url':
        'https://download.opensuse.org/repositories/'
        'Virtualization:/Appliances:/Builder',
    'author_email': 'dcassany@suse.com',
    'version': __version__,
    'license' : 'GPLv3+',
    'install_requires': [
        'kiwi>=9.23.0'
    ],
    'packages': ['kiwi_rebuild_plugin'],
    'entry_points': {
        'kiwi.tasks': [
            'system_rebuild=kiwi_rebuild_plugin.tasks.system_rebuild'
        ]
    },
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
       # classifier: http://pypi.python.org/pypi?%3Aaction=list_classifiers
       'Development Status :: 5 - Production/Stable',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: '
       'GNU General Public License v3 or later (GPLv3+)',
       'Operating System :: POSIX :: Linux',
       'Programming Language :: Python :: 3.6',
       'Programming Language :: Python :: 3.7',
       'Topic :: System :: Operating System',
    ]
}

setup(**config)
