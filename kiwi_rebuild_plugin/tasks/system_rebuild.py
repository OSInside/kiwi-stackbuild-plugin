# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms owf the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
"""
usage: kiwi-ng system rebuild -h | --help
       kiwi-ng system rebuild --root-tree=<image-ref>
           [--description=<directory>]
           [--keep-root=<image-ref>]
           <kiwi_build_command_args>...
       kiwi-ng system rebuild --description=<directory>
           [--root-tree=<image-ref>]
           [--keep-root=<image-ref>]
           <kiwi_build_command_args>...

commands:
    rebuild
        build a system image from the specified description and/or from the
        specified prestored root tree. The rebuild command combines the
        prepare and create commands. Alternatively, it can also run a regular
        build and and store the root tree for later use.

options:
    --root-tree=<image_ref>
        it must be an image reference containing a root-tree from a previous
        kiwi build

    --keep-root=<image-ref>
        image reference of to keep

    <kiwi_build_command_args>...
        List of command parameters as supported by the kiwi-ng
        build command.
"""
import os
import sys
import logging
import kiwi.tasks.system_build

from tempfile import mkdtemp
from docopt import docopt
from unittest.mock import patch
from kiwi.help import Help
from kiwi.privileges import Privileges
from kiwi.tasks.system_prepare import SystemPrepareTask
from kiwi.tasks.system_create import SystemCreateTask
from kiwi.tasks.base import CliTask
from kiwi.path import Path

# project
from kiwi_rebuild_plugin.root_cache import RootCacheOCI
from kiwi_rebuild_plugin.xml_merge import XMLMerge


log = logging.getLogger('kiwi')


class SystemRebuildTask(CliTask):
    def __init__(self, should_perform_task_setup=True):
        super().__init__(should_perform_task_setup)
        self.manual = Help()
        self.temp_desc = self.temp_desc = mkdtemp(prefix='kiwi_description.')
        self.build_command_args = self._get_build_command_args() 

    def process(self):
        if self.build_command_args['help']:
            self.manual.show('kiwi::system::build')
            return

        Privileges.check_for_root_permissions()

        abs_target_dir_path = os.path.abspath(
            self.build_command_args['--target-dir']
        )
        build_dir = os.sep.join([abs_target_dir_path, 'build'])
        image_root = os.sep.join([build_dir, 'image-root'])
        Path.create(build_dir)

        if not self.global_args['--logfile']:
            log.set_logfile(
                os.sep.join([abs_target_dir_path, 'build', 'image-root.log'])
            )

        description = self.command_args['--description']
        keep_root = self.command_args['--keep-root']
        if self.command_args['--root-tree']:
            Path.wipe(image_root)
            self.build_command_args['--allow-existing-root'] = True
            root_tree = RootCacheOCI(image_root)
            root_tree.import_root(self.command_args['--root-tree'])
            root_tree.import_description(self.temp_desc)
            if description:
                merger = XMLMerge(description, self.temp_desc)
                merger.merge_description()
            self.build_command_args['--description'] = self.temp_desc
        else:
            self.build_command_args['--description'] = description

        if description:
            with patch.object(
                sys, 'argv', self.system_prepare_args_list(image_root)
            ):
                system_prepare = SystemPrepareTask(
                    should_perform_task_setup=False
                )
                system_prepare.process()

        with patch.object(
            sys, 'argv', self.system_create_args_list(image_root)
        ):
            system_create = SystemCreateTask(should_perform_task_setup=False)
            system_create.process()

        if keep_root:
            log.info('Storing rootfs in an OCI artifact')
            transport, repo, tag = self.parse_keep_root(keep_root)
            root_cache = RootCacheOCI(image_root)
            if repo:
                repo = f'{repo}/{self.xml_state.xml_data.get_name()}'
            else:
                repo = self.xml_state.xml_data.get_name()
            if not tag:
                tag = self.xml_state.get_image_version() 
            root_cache.store_root(
                transport, repo, tag,
                self.xml_state.get_description_section().author,
                abs_target_dir_path
            )

    def system_prepare_args_list(self, root):
        prepare_args = self.build_command_args.copy()
        prepare_args.pop('system')
        prepare_args.pop('build')
        prepare_args.pop('--target-dir')
        prepare_args['--root'] = root
        prepare_args_lst = ['kiwi-ng']
        prepare_args_lst.extend(self._opts_to_list(self.global_args))
        prepare_args_lst.extend(['system', 'prepare'])
        return prepare_args_lst + self._opts_to_list(prepare_args)

    def system_create_args_list(self, root):
        create_args = {
            '--root': root,
            '--target-dir': self.build_command_args['--target-dir']
        }
        if self.build_command_args['--signing-key']:
            create_args['--signing-key'] = self.build_command_args[
                '--signing-key'
            ]
        create_args_lst = ['kiwi-ng']
        create_args_lst.extend(self._opts_to_list(self.global_args))
        create_args_lst.extend(['system', 'create'])
        return create_args_lst + self._opts_to_list(create_args)

    def _get_build_command_args(self):
        kiwi_build_command = [
            'system', 'build'
        ]
        kiwi_build_command += self.command_args.get(
            '<kiwi_build_command_args>'
        )
        if '--' in kiwi_build_command:
            kiwi_build_command.remove('--')
        if '--description' in kiwi_build_command:
            raise Exception("duplicated description option")

        # Just to ensure we pass system build command validation
        kiwi_build_command.extend(['--description', self.temp_desc])

        log.info(
            'Validating kiwi_build_command_args:{0}    {1}'.format(
                os.linesep, kiwi_build_command
            )
        )
        return docopt(
            doc=kiwi.tasks.system_build.__doc__,
            argv=kiwi_build_command
        )

    def _opts_to_list(self, opts_dict):
        opts_lst = []
        for k, v in opts_dict.items():
            if not k.startswith('-'):
                continue
            if isinstance(v, bool) and v is True:
                opts_lst.append(k)
            elif isinstance(v, str):
                opts_lst.extend([k,v])
            elif isinstance(v, list) and v:
                for it in v:
                    opts_lst.extend([k, it])
            else:
                continue
        return opts_lst

    def _parse_keep_root(self, keep_root):
        part = keep_root.partition(':')
        transport = part[0]
        tag = ''
        repo = ''
        if part[2]:
            part = part[2].rpartition(':')
            tag = part[2]
            repo = part[0]
        return (transport, repo, tag)

    def __del__(self):
        Path.wipe(self.temp_desc)
