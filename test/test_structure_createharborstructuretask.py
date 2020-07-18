import os
import tempfile
from harbor.test import BaseHarborTestClass
from harbor.tasks.structure import CreateHarborStructureTask


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
                # do not match current dev version as it may be unreleased yet when developing
                task.get_harbor_version_matcher = lambda: ''

                self.execute_task(task, args={
                    '--commit': False,
                    '--no-venv': False
                })

                self.assertTrue(os.path.isfile(dir_path + '/.env-default'),
                                msg='Expected that dot files will be copied')

                self.assertTrue(os.path.isfile(dir_path + '/.venv/bin/activate'),
                                msg='Expected the virtualenv to be installed')

                self.assertTrue(os.path.isfile(dir_path + '/apps/README.md'),
                                msg='Expected that files in inner directories will be present')

                with open(dir_path + '/requirements.txt', 'rb') as requirements_txt:
                    content = requirements_txt.read().decode('utf-8')

                    self.assertIn('ansible>=2.8', content, msg='Expected Ansible defined in requirements.txt')
                    self.assertIn('rkd-harbor', content, msg='Expected rkd-harbor to be defined in requirements.txt')
        finally:
            os.chdir(backup_dir_path)

