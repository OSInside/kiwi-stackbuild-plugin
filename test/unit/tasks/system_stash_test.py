import sys
from mock import (
    Mock, patch
)

from kiwi_stackbuild_plugin.tasks.system_stash import SystemStashTask


class TestSystemStashTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], 'system', 'stash',
            '--root', 'some-root-dir'
        ]
        self.task = SystemStashTask()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['stash'] = False
        self.task.command_args['--root'] = None
        self.task.command_args['--tag'] = None

    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Help')
    def test_process_help(self, mock_Help):
        Help = Mock()
        mock_Help.return_value = Help
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['stash'] = True
        self.task.process()
        Help.show.assert_called_once_with(
            'kiwi::system::stash'
        )

    @patch('kiwi_stackbuild_plugin.tasks.system_stash.OCI.new')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Path')
    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_process_build_initial_layer(
        self, mock_os_path_abspath, mock_os_path_exists,
        mock_Path, mock_Privileges, mock_OCI_new
    ):
        self._init_command_args()
        self.task.command_args['--root'] = '../data/image-root'
        oci = Mock()
        mock_OCI_new.return_value = oci
        mock_os_path_exists.return_value = False
        mock_os_path_abspath.return_value = 'absolute_root_dir_path'
        container_config = {
            'container_name': 'stash.tar',
            'container_tag': 'tumbleweed',
            'entry_command': ['/bin/sh'],
            'labels': {
                'io.osinside.kiwi.maintainer': 'Marcus Schaefer',
                'io.osinside.kiwi.meta':
                    'KIWI - https://github.com/OSInside/kiwi'
            },
            'history': {
                'created_by':
                    'KIWI - https://github.com/OSInside/kiwi',
                'comment': 'KIWI Root Tree Stash',
                'author': 'Marcus Schaefer'
            }
        }
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.task.process()
            mock_Privileges.check_for_root_permissions.assert_called_once_with()
            oci.init_container.assert_called_once_with()
            oci.unpack.assert_called_once_with()
            oci.sync_rootfs.assert_called_once_with(
                '../data/image-root', ['dev/*', 'sys/*', 'proc/*']
            )
            oci.repack.assert_called_once_with(container_config)
            oci.set_config.assert_called_once_with(container_config)
            oci.post_process.assert_called_once_with()
            oci.export_container_image.assert_called_once_with(
                '../data/.config/kiwi_stash/tumbleweed/stash.tar',
                'oci-archive', 'tumbleweed'
            )

    @patch('kiwi_stackbuild_plugin.tasks.system_stash.OCI.new')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Path')
    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_process_build_additional_layer(
        self, mock_os_path_abspath, mock_os_path_exists,
        mock_Path, mock_Privileges, mock_OCI_new
    ):
        self._init_command_args()
        self.task.command_args['--root'] = '../data/image-root'
        oci = Mock()
        mock_OCI_new.return_value = oci
        mock_os_path_exists.return_value = True
        mock_os_path_abspath.return_value = 'absolute_root_dir_path'
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.task.process()
            oci.import_container_image.assert_called_once_with(
                'oci-archive:../data/.config/kiwi_stash/'
                'tumbleweed/stash.tar:tumbleweed'
            )
