import sys
import shutil
from pytest import raises
from tempfile import mkdtemp
from mock import (
    Mock, patch, call
)

from kiwi_stackbuild_plugin.tasks.system_stackbuild import SystemStackbuildTask
from kiwi_stackbuild_plugin.exceptions import (
    KiwiStackBuildPluginTargetDirExists,
    KiwiStackBuildPluginRootSyncFailed
)


class TestSystemStackbuildTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'a', '--profile', 'b',
            '--type', 'iso', 'system', 'stackbuild',
            '--stash', 'name', '--target-dir', 'some-target-dir', '--',
            '--signing-key', 'some-key'
        ]
        self.task = SystemStackbuildTask()
        self.target_dir = mkdtemp(prefix='kiwi_test_target.')

    def setup_method(self, cls):
        self.setup()

    def teardown_method(self, cls):
        shutil.rmtree(self.target_dir)

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['stackbuild'] = False
        self.task.command_args['--stash'] = []
        self.task.command_args['--from-registry'] = None
        self.task.command_args['--target-dir'] = None
        self.task.command_args['--description'] = None
        self.task.command_args['<kiwi_build_command_args>'] = [
            '--', '--signing-key', 'some-key'
        ]
        self.task.command_args['<kiwi_create_command_args>'] = [
            '--', '--signing-key', 'some-key'
        ]

    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Help')
    def test_process_help(self, mock_Help):
        Help = Mock()
        mock_Help.return_value = Help
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['stackbuild'] = True
        self.task.process()
        Help.show.assert_called_once_with(
            'kiwi::system::stackbuild'
        )

    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Privileges')
    @patch('os.path.exists')
    def test_process_target_dir_exists(
        self, mock_os_path_exists, mock_Privileges
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        mock_os_path_exists.return_value = True
        with raises(KiwiStackBuildPluginTargetDirExists):
            self.task.process()

    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.DataSync')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Path.create')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Command.run')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.SystemCreateTask')
    @patch('os.path.exists')
    def test_process_root_sync_failed(
        self, mock_os_path_exists, mock_SystemCreateTask, mock_Command_run,
        mock_Path_create, mock_Privileges, mock_DataSync
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        mock_os_path_exists.return_value = False

        mock_DataSync.side_effect = Exception

        kiwi_task = Mock()
        mock_SystemCreateTask.return_value = kiwi_task
        with raises(KiwiStackBuildPluginRootSyncFailed):
            self.task.process()

    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Path.create')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Command.run')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.SystemCreateTask')
    @patch('os.path.exists')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.patch.object')
    def test_process_rebuild(
        self, mock_patch_object, mock_os_path_exists,
        mock_SystemCreateTask, mock_Command_run,
        mock_Path_create, mock_Privileges
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = '/some/target-dir'
        self.task.command_args['--from-registry'] = 'registry.uri'
        mock_os_path_exists.return_value = False
        mock_Command_run.return_value.output = '/podman/mount/path'
        kiwi_task = Mock()
        mock_SystemCreateTask.return_value = kiwi_task
        self.task.process()
        assert mock_Command_run.call_args_list == [
            call(['podman', 'pull', 'registry.uri/name']),
            call(['podman', 'image', 'mount', 'name']),
            call(
                [
                    'rsync', '--archive', '--hard-links', '--xattrs',
                    '--acls', '--one-file-system', '--inplace',
                    '/podman/mount/path/',
                    '/some/target-dir/build/image-root'
                ]
            ),
            call(
                ['podman', 'image', 'umount', '--force', 'name'],
                raise_on_error=False
            )
        ]
        mock_SystemCreateTask.assert_called_once_with(
            should_perform_task_setup=False
        )
        kiwi_task.process.assert_called_once_with()
        mock_patch_object.assert_called_once_with(
            sys, 'argv', [
                'kiwi-ng', '--type', 'iso',
                '--profile', 'a', '--profile', 'b',
                'system', 'create',
                '--root', '/some/target-dir/build/image-root',
                '--target-dir', '/some/target-dir',
                '--signing-key', 'some-key'
            ]
        )

    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Path.create')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Command.run')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.SystemBuildTask')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.patch.object')
    def test_process_new_kiwi_build(
        self, mock_patch_object,
        mock_SystemBuildTask, mock_Command_run,
        mock_Path_create, mock_Privileges
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = self.target_dir
        self.task.command_args['--description'] = '../data/kiwi-description'
        self.task.command_args['--from-registry'] = 'registry.uri'
        mock_Command_run.return_value.output = '/podman/mount/path'
        kiwi_task = Mock()
        mock_SystemBuildTask.return_value = kiwi_task
        self.task.process()
        assert mock_Command_run.call_args_list == [
            call(['podman', 'pull', 'registry.uri/name']),
            call(['podman', 'image', 'mount', 'name']),
            call(
                [
                    'rsync', '--archive', '--hard-links', '--xattrs',
                    '--acls', '--one-file-system', '--inplace',
                    '/podman/mount/path/',
                    f'{self.target_dir}/build/image-root'
                ]
            ),
            call(
                ['podman', 'image', 'umount', '--force', 'name'],
                raise_on_error=False
            )
        ]
        mock_SystemBuildTask.assert_called_once_with(
            should_perform_task_setup=False
        )
        kiwi_task.process.assert_called_once_with()
        mock_patch_object.assert_called_once_with(
            sys, 'argv', [
                'kiwi-ng', '--type', 'iso',
                '--profile', 'a', '--profile', 'b',
                'system', 'build',
                '--description', '../data/kiwi-description',
                '--target-dir', self.target_dir,
                '--allow-existing-root', '--signing-key', 'some-key'
            ]
        )

    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.TemporaryDirectory')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.XMLMerge')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Privileges')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Path.create')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.Command.run')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.SystemBuildTask')
    @patch('kiwi_stackbuild_plugin.tasks.system_stackbuild.patch.object')
    def test_process_new_stackbuild_build(
        self, mock_patch_object, mock_SystemBuildTask,
        mock_Command_run, mock_Path_create, mock_Privileges,
        mock_XMLMerge, mock_TemporaryDirectory
    ):
        self._init_command_args()
        self.task.command_args['stackbuild'] = True
        self.task.command_args['--stash'] = ['name']
        self.task.command_args['--target-dir'] = self.target_dir
        self.task.command_args['--description'] = '../data/stackbuild-description'
        self.task.command_args['--from-registry'] = 'registry.uri'
        mock_Command_run.return_value.output = '/podman/mount/path'
        stackbuild_check = Mock()
        stackbuild_check.return_value = True
        mock_XMLMerge.is_stackbuild_description = stackbuild_check
        mock_TemporaryDirectory.return_value.__enter__.return_value = '/temporary/merged/description'
        kiwi_task = Mock()
        mock_SystemBuildTask.return_value = kiwi_task
        self.task.process()
        assert mock_Command_run.call_args_list == [
            call(['podman', 'pull', 'registry.uri/name']),
            call(['podman', 'image', 'mount', 'name']),
            call(
                [
                    'rsync', '--archive', '--hard-links', '--xattrs',
                    '--acls', '--one-file-system', '--inplace',
                    '/podman/mount/path/',
                    f'{self.target_dir}/build/image-root'
                ]
            ),
            call(
                ['podman', 'image', 'umount', '--force', 'name'],
                raise_on_error=False
            )
        ]
        mock_SystemBuildTask.assert_called_once_with(
            should_perform_task_setup=False
        )
        kiwi_task.process.assert_called_once_with()
        mock_patch_object.assert_called_once_with(
            sys, 'argv', [
                'kiwi-ng', '--type', 'iso',
                '--profile', 'a', '--profile', 'b',
                'system', 'build',
                '--description', '/temporary/merged/description',
                '--target-dir', self.target_dir,
                '--allow-existing-root', '--signing-key', 'some-key'
            ]
        )
