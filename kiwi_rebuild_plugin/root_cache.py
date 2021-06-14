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
import os
import json
from kiwi.oci_tools import OCI
from kiwi.utils.sync import DataSync
from kiwi.defaults import Defaults
from kiwi.command import Command


class RootCacheOCI:
    """
    Create OCI container containing the root tree created by KIWI

    :param str root_dir: root directory path name
    """
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.metadata = 'Some metadata check'  # TODO

    def store_root(self, transport, repo, tag, maintainer, target_dir):
        filename = ''
        if transport.endswith('archive'):
            repo_part = repo.partition(':')
            if not repo[0] or not repo[2]:
                raise Exception(
                    'Invalid repository section for archive transport'
                )
            repo = repo_part[2]
            filename = repo_part[0]

        exclude_list = ['dev/*', 'sys/*', 'proc/*']
        container_args = {
            'container_name': repo,
            'container_tag': tag,
            'entry_command': ['/bin/sh'],
            'labels': {
                'io.osinside.kiwi.maintainer': maintainer,
                'io.osinside.kiwi.meta': self.metadata
            }, 'history': {
                'created_by': "KIWI prepare step",
                'comment': "Root tree cache of a KIWI build",
                'author': maintainer
            }
        }

        oci = OCI.new()
        oci.init_container()

        oci.unpack()
        oci.sync_rootfs(self.root_dir, exclude_list)
        oci.repack(container_args)
        oci.set_config(container_args)
        oci.post_process()

        if filename:
            oci.export_container_image(
                filename, transport, f'{repo}:{tag}'
            )
        else:
            oci.export_container_image(repo, transport, tag)

    def import_root(self, image_uri):
        self.check_kiwi_tree(image_uri)
        oci = OCI.new()
        oci.import_container_image(image_uri)
        oci.unpack()
        oci.import_rootfs(self.root_dir)

    def import_description(self, desc_dir):
        sync = DataSync(os.sep.join([self.root_dir, 'image/']), desc_dir)
        sync.sync_data(options=Defaults.get_sync_options())

    def check_kiwi_tree(self, image_uri):
        output = Command.run(['skopeo', 'inspect', image_uri])
        meta = json.loads(output.output)
        if 'Labels' in meta and 'io.osinside.kiwi.meta' in meta['Labels']:
            return
        raise Exception("This is not a valid image")
