# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi-stackbuild.
#
# kiwi-stackbuild is free software: you can redistribute it and/or modify
# it under the terms owf the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi-stackbuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi-stackbuild.  If not, see <http://www.gnu.org/licenses/>
#
"""
usage: kiwi-ng system stackbuild -h | --help
       kiwi-ng system stackbuild --stash=<name> --description=<directory> --target-dir=<directory>
           [--from-registry=<URI>]
           [-- <kiwi_build_command_args>...]
       kiwi-ng system stackbuild --stash=<name> --target-dir=<directory>
           [--from-registry=<URI>]
           [-- <kiwi_create_command_args>...]
       kiwi-ng system stackbuild help

commands:
    stackbuild
        build an image based on a given stash container root. If no
        KIWI description is provided along with the command, stackbuild
        rebuilds the image from the stash container. If a KIWI
        description is provided, this description takes over precedence
        and a new image from this description based on the given stash
        container root will be built.
    stackbuild help
        show manual page for stackbuild command

options:
    --stash=<name>
        Name of the stash container. See 'system stash --list'
        for available stashes

    --from-registry=<URI>
        Pull given stash container name from the provided
        registry URI

    --description=<directory>
        Path to KIWI image description

    --target-dir=<directory>
        the target directory to store the system image file(s)

    <kiwi_build_command_args>...
        List of command parameters as supported by
        'system build' command.

    <kiwi_create_command_args>...
        List of command parameters as supported by the
        'system create' command.
"""
import os
import sys
import logging
from mock import patch
from docopt import docopt
from typing import (
    Dict, List
)

import kiwi.tasks.system_build
import kiwi.tasks.system_create

from kiwi.help import Help
from kiwi.privileges import Privileges
from kiwi.tasks.base import CliTask
from kiwi.tasks.system_create import SystemCreateTask
from kiwi.tasks.system_build import SystemBuildTask
from kiwi.command import Command
from kiwi.path import Path
from kiwi.utils.sync import DataSync
from kiwi.defaults import Defaults

from kiwi_stackbuild_plugin.exceptions import (
    KiwiStackBuildPluginTargetDirExists
)

log = logging.getLogger('kiwi')


class SystemStackbuildTask(CliTask):
    def process(self) -> None:
        self.manual = Help()
        if self.command_args.get('help') is True:
            return self.manual.show('kiwi::system::stackbuild')

        Privileges.check_for_root_permissions()

        if self.command_args.get('--stash'):
            stash_name = self.command_args['--stash']
            image_root_dir = os.path.join(
                self.command_args['--target-dir'], 'build', 'image-root'
            )
            if os.path.exists(image_root_dir):
                raise KiwiStackBuildPluginTargetDirExists(
                    f'image root dir: {image_root_dir!r} already exists'
                )
            Path.create(image_root_dir)
            if self.command_args['--from-registry']:
                log.info(
                    'Fetching stash {0!r} from registry {1!r}'.format(
                        stash_name,
                        self.command_args['--from-registry']
                    )
                )
                Command.run(
                    [
                        'podman', 'pull', os.path.join(
                            self.command_args['--from-registry'],
                            stash_name
                        )
                    ]
                )
            log.info(f'Mounting stash: {stash_name!r}')
            stash_mount_point = Command.run(
                ['podman', 'image', 'mount', stash_name]
            ).output.strip()
            root = DataSync(
                stash_mount_point + os.sep, image_root_dir
            )
            log.info(
                'Syncing stash root {0!r} to image root {1!r}'.format(
                    stash_mount_point, image_root_dir
                )
            )
            root.sync_data(
                options=Defaults.get_sync_options()
            )
            log.info(f'Umount stash: {stash_name!r}')
            Command.run(
                ['podman', 'image', 'umount', stash_name]
            )
            if self.command_args.get('--description'):
                with patch.object(
                    sys, 'argv', self._validate_kiwi_build_command(
                        [
                            'system', 'build',
                            '--description', self.command_args['--description'],
                            '--target-dir', self.command_args['--target-dir'],
                            '--allow-existing-root'
                        ]
                    )
                ):
                    kiwi_task = SystemBuildTask(
                        should_perform_task_setup=False
                    )
            else:
                with patch.object(
                    sys, 'argv', self._validate_kiwi_create_command(
                        [
                            'system', 'create',
                            '--root', image_root_dir,
                            '--target-dir', self.command_args['--target-dir']
                        ]
                    )
                ):
                    kiwi_task = SystemCreateTask(
                        should_perform_task_setup=False
                    )

            kiwi_task.process()

    def _validate_kiwi_create_command(
        self, kiwi_create_command: List[str]
    ) -> List[str]:
        # construct create command from given command line
        kiwi_create_command += self.command_args.get(
            '<kiwi_create_command_args>'
        )
        if '--' in kiwi_create_command:
            kiwi_create_command.remove('--')
        # validate create command through docopt from the original
        # kiwi.tasks.system_create docopt information
        log.debug(
            'Validating kiwi_create_command_args:{0}    {1}'.format(
                os.linesep, kiwi_create_command
            )
        )
        validated_create_command = docopt(
            doc=kiwi.tasks.system_create.__doc__,
            argv=kiwi_create_command
        )
        # rebuild kiwi create command from validated docopt parser result
        return self._rebuild_kiwi_command(
            validated_create_command, 'create'
        )

    def _validate_kiwi_build_command(
        self, kiwi_build_command: List[str]
    ) -> List[str]:
        # construct build command from given command line
        kiwi_build_command += self.command_args.get(
            '<kiwi_build_command_args>'
        )
        if '--' in kiwi_build_command:
            kiwi_build_command.remove('--')
        # validate build command through docopt from the original
        # kiwi.tasks.system_build docopt information
        log.debug(
            'Validating kiwi_build_command_args:{0}    {1}'.format(
                os.linesep, kiwi_build_command
            )
        )
        validated_build_command = docopt(
            doc=kiwi.tasks.system_build.__doc__,
            argv=kiwi_build_command
        )
        # rebuild kiwi build command from validated docopt parser result
        return self._rebuild_kiwi_command(
            validated_build_command, 'build'
        )

    def _rebuild_kiwi_command(
        self, validated_options_dict: Dict, command: str
    ) -> List[str]:
        kiwi_command = [
            'system', command
        ]
        for option, value in validated_options_dict.items():
            if option.startswith('-') and value:
                if isinstance(value, bool):
                    kiwi_command.append(option)
                elif isinstance(value, str):
                    kiwi_command.extend([option, value])
                elif isinstance(value, list):
                    for element in value:
                        kiwi_command.extend([option, element])
        final_kiwi_command = ['kiwi-ng']
        if self.global_args.get('--type'):
            final_kiwi_command.append('--type')
            final_kiwi_command.append(self.global_args.get('--type'))
        if self.global_args.get('--profile'):
            for profile in sorted(set(self.global_args.get('--profile'))):
                final_kiwi_command.append('--profile')
                final_kiwi_command.append(profile)
        final_kiwi_command += kiwi_command
        log.debug(
            'Building with:{0}    {1}'.format(
                os.linesep, final_kiwi_command
            )
        )
        return final_kiwi_command
