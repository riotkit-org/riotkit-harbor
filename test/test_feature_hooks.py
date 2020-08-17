import os
import subprocess
from io import StringIO
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.inputoutput import IO
from rkd.api.contract import ExecutionContext
from rkd.api.syntax import TaskDeclaration
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.test import TestTask


class TestHooksFeature(BaseHarborTestClass):
    def _prepare_test_data(self):
        with open(self.get_test_env_subdirectory('hooks.d/pre-upgrade') + '/whoami.sh', 'w') as fw:
            fw.write('''
                #!/bin/bash
                echo " >> This is a whoami.sh hook, test: $(whoami)"
            ''')

        with open(self.get_test_env_subdirectory('hooks.d/post-upgrade') + '/history.sh', 'w') as fw:
            fw.write('''
                #!/bin/bash
                echo "25 June 1978 the rainbow flag was first flown at the San Francisco Gay Freedom Day Parade. The flag was designed by artist Gilbert Baker, and hand-dyed and stitched by 30 volunteers."
            ''')

        subprocess.check_call(['chmod', '+x', self.get_test_env_subdirectory('hooks.d/pre-upgrade') + '/whoami.sh'])
        subprocess.check_call(['chmod', '+x', self.get_test_env_subdirectory('hooks.d/post-upgrade') + '/history.sh'])

    def test_functional_hooks_are_executed_when_exists_and_files_with_extension_only_are_skipped(self):
        """Given we have an example hooks in pre-upgrade/whoami.sh and in post-upgrade/history.sh
        And we try to run those hooks using hooks_executed()
        Then we will see output produced by those scripts
        And .dotfiles will be ignored
        """

        self._prepare_test_data()

        buffer = StringIO()
        hooks_capturing_io = IO()

        task = TestTask()
        task._io = BufferedSystemIO()
        ctx = ExecutionContext(
            TaskDeclaration(task),
            args={},
            env={}
        )

        with hooks_capturing_io.capture_descriptors(stream=buffer, enable_standard_out=True):
            with task.hooks_executed(ctx, 'upgrade'):
                pass

        self.assertIn('>> This is a whoami.sh hook, test:', buffer.getvalue(),
                      msg='Expected pre-upgrade hook to be ran')

        self.assertIn('25 June 1978 the rainbow flag was first flown', buffer.getvalue(),
                      msg='Expected post-upgrade hook to be ran')

        self.assertIn('pre-upgrade/whoami.sh', task._io.get_value())
        self.assertNotIn('.gitkeep', task._io.get_value())

    def test_functional_execute_hooks_executes_post_upgrade_hooks(self):
        """Assert that post-upgrade/history.sh is executed"""

        self._prepare_test_data()

        buffer = StringIO()
        hooks_capturing_io = IO()

        task = TestTask()
        task._io = BufferedSystemIO()
        ctx = ExecutionContext(
            TaskDeclaration(task),
            args={},
            env={}
        )

        with hooks_capturing_io.capture_descriptors(stream=buffer, enable_standard_out=True):
            task.execute_hooks(ctx, 'post-upgrade')

        self.assertIn('25 June 1978 the rainbow flag was first flown', buffer.getvalue(),
                      msg='Expected post-upgrade hook to be ran')

    def test_non_existing_dir_is_skipped(self):
        """Assert that non-existing directory does not cause exception, but will be skipped"""

        task = TestTask()
        task._io = BufferedSystemIO()
        task._io.set_log_level('debug')
        ctx = ExecutionContext(
            TaskDeclaration(task),
            args={},
            env={}
        )

        task.execute_hooks(ctx, 'non-existing-directory')
        self.assertIn('Hooks dir "./hooks.d//non-existing-directory/" not present, skipping', task._io.get_value())

