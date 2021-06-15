#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup

from kiwi_stackbuild_plugin.version import __version__


config = {
    'name': 'kiwi_stackbuild_plugin',
    'description': 'KIWI - Stack Build Plugin',
    'author': 'David Cassany',
    'author': 'Marcus Schäfer',
    'url': 'https://github.com/OSInside/kiwi-stackbuild-plugin',
    'download_url':
        'https://download.opensuse.org/repositories/'
        'Virtualization:/Appliances:/Builder',
    'author_email': 'dcassany@suse.com',
    'author_email': 'ms@suse.com',
    'version': __version__,
    'license' : 'GPLv3+',
    'install_requires': [
        'docopt',
        'kiwi>=9.23.0'
    ],
    'packages': ['kiwi_stackbuild_plugin'],
    'entry_points': {
        'kiwi.tasks': [
            'system_stackbuild=kiwi_stackbuild_plugin.tasks.system_stackbuild'
        ]
    },
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
       # classifier: http://pypi.python.org/pypi?%3Aaction=list_classifiers
       # 'Development Status :: 5 - Production/Stable',
       'Development Status :: 2 - Pre-Alpha',
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
