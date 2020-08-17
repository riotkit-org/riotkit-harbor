import os
import tempfile
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.structure import CreateHarborStructureTask
from rkd.api.contract import ExecutionContext
from rkd.api.inputoutput import IO
from rkd.test import get_test_declaration


class CreateHarborStructureTaskTest(BaseHarborTestClass):

    def test_functional_installation(self):
        """Test functionally that the structure will be created properly

        NOTICE: This test has external dependencies such as PyPI
        """

        backup_dir_path = os.getcwd()

        try:
            with tempfile.TemporaryDirectory() as dir_path:
                os.chdir(dir_path)

                task = CreateHarborStructureTask()

                # do not write requirements.txt in tests, we do not want to install all of those things
                # as it is very problematic in development environment where things are "under construction"
                task.on_requirements_txt_write = lambda ctx: None

                self.execute_task(task, args={
                    '--commit': False,
                    '--no-venv': False,
                    '--pipenv': False
                })

                self.assertTrue(os.path.isfile(dir_path + '/.env-default'),
                                msg='Expected that dot files will be copied')

                self.assertTrue(os.path.isfile(dir_path + '/.venv/bin/activate'),
                                msg='Expected the virtualenv to be installed')

                self.assertTrue(os.path.isfile(dir_path + '/apps/README.md'),
                                msg='Expected that files in inner directories will be present')

        finally:
            os.chdir(backup_dir_path)

    def test_requirements_are_written(self):
        """Verify that basic requirements list is written into requirements.txt file"""

        backup_dir_path = os.getcwd()

        try:
            with tempfile.TemporaryDirectory() as dir_path:
                os.chdir(dir_path)

                task = CreateHarborStructureTask()
                task._io = IO()
                task.on_requirements_txt_write(ExecutionContext(get_test_declaration()))

                with open(dir_path + '/requirements.txt', 'rb') as requirements_txt:
                    content = requirements_txt.read().decode('utf-8')

                    self.assertIn('ansible>=2.8', content, msg='Expected Ansible defined in requirements.txt')
                    self.assertIn('rkd-harbor==', content, msg='Expected rkd-harbor to be defined in requirements.txt')

        finally:
            os.chdir(backup_dir_path)
