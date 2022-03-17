import sys
from pytest import raises
from mock import (
    Mock, patch
)

from kiwi_stackbuild_plugin.tasks.system_stash import SystemStashTask
from kiwi_stackbuild_plugin.exceptions import (
    KiwiStackBuildPluginContainerNameInvalid
)


class TestSystemStashTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], 'system', 'stash',
            '--root', 'some-root-dir'
        ]
        self.task = SystemStashTask()

    def setup_method(self, cls):
        self.setup()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['stash'] = False
        self.task.command_args['--root'] = None
        self.task.command_args['--tag'] = None
        self.task.command_args['--container-name'] = None

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

    @patch('kiwi_stackbuild_plugin.tasks.system_stash.DataOutput')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Privileges')
    @patch('os.listdir')
    def test_process_stash_list(
        self, mock_os_listdir, mock_Privileges, mock_DataOutput
    ):
        mock_os_listdir.return_value = ['name']
        stashes = Mock()
        mock_DataOutput.return_value = stashes
        self._init_command_args()
        self.task.command_args['stash'] = True
        self.task.command_args['--list'] = True
        self.task.process()
        stashes.display.assert_called_once_with()

    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Privileges')
    def test_process_invalid_container_name(self, mock_Privileges):
        self._init_command_args()
        self.task.command_args['--root'] = '../data/image-root-invalid-name'
        with raises(KiwiStackBuildPluginContainerNameInvalid):
            self.task.process()

    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Command.run')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.OCI.new')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Path')
    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_process_build_initial_layer(
        self, mock_os_path_abspath, mock_os_path_exists,
        mock_Path, mock_Privileges, mock_OCI_new, mock_Command_run
    ):
        def os_path_exists(filename):
            if filename == '/var/tmp/kiwi-stash/tumbleweed/tumbleweed.tar':
                return False
            else:
                return True

        self._init_command_args()
        self.task.command_args['--root'] = '../data/image-root'
        oci = Mock()
        mock_OCI_new.return_value = oci
        mock_os_path_exists.side_effect = os_path_exists
        mock_os_path_abspath.return_value = 'absolute_root_dir_path'
        container_config = {
            'container_name': 'tumbleweed',
            'container_tag': 'latest',
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
            '/var/tmp/kiwi-stash/tumbleweed/tumbleweed.tar',
            'oci-archive', 'tumbleweed:latest'
        )
        mock_Command_run.assert_called_once_with(
            [
                'podman', 'load', '-i',
                '/var/tmp/kiwi-stash/tumbleweed/tumbleweed.tar'
            ]
        )

    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Command.run')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.OCI.new')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stash.Path')
    @patch('os.path.exists')
    @patch('os.path.abspath')
    def test_process_build_additional_layer(
        self, mock_os_path_abspath, mock_os_path_exists,
        mock_Path, mock_Privileges, mock_OCI_new, mock_Command_run
    ):
        self._init_command_args()
        self.task.command_args['--root'] = '../data/image-root'
        oci = Mock()
        mock_OCI_new.return_value = oci
        mock_os_path_exists.return_value = True
        mock_os_path_abspath.return_value = 'absolute_root_dir_path'
        self.task.process()
        oci.import_container_image.assert_called_once_with(
            'oci-archive:/var/tmp/kiwi-stash/'
            'tumbleweed/tumbleweed.tar:tumbleweed:latest'
        )
        mock_Command_run.assert_called_once_with(
            [
                'podman', 'load', '-i',
                '/var/tmp/kiwi-stash/tumbleweed/tumbleweed.tar'
            ]
        )
