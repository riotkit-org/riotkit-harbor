import os
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.deployment.apply import CreateExampleDeploymentFileTask


class CreateExampleDeploymentFileTaskTest(BaseHarborTestClass):
    def test_functional_example_deployment_file_is_created_if_it_does_not_exists(self):
        """Verify that the structure is copied, and the files are rendered using JINJA2"""

        self.execute_task(CreateExampleDeploymentFileTask(), args={}, env={})
        self.assertTrue(os.path.isfile(self.get_test_env_subdirectory('') + '/deployment.yml'))

    def test_functional_example_deployment_cannot_be_created_twice(self):
        """Test that file created once cannot be overridden"""

        # prepare test data
        path = self.get_test_env_subdirectory('') + '/deployment.yml'
        with open(path, 'wb') as f:
            f.write('test: true'.encode('utf-8'))

        # execute action
        out = self.execute_task(CreateExampleDeploymentFileTask(), args={}, env={})

        # verify
        self.assertIn('deployment.yml or deployment.yaml already exists', out, msg='Expected error message')

        with open(path, 'rb') as f:
            self.assertIn('test: true', f.read().decode('utf-8'), msg='Original content should be there')
