import os
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.deployment.syncfiles import UpdateFilesTask


class UpdateFilesTaskTest(BaseHarborTestClass):
    def test_functional_validates_deployment_yml_file_not_created(self):
        """Test that deployment.yml/deployment.yaml needs to be created first and the message for the end user is clear
        """

        out = self.execute_task(UpdateFilesTask(), args={'--ask-vault-pass': False, '--vault-passwords': ''}, env={})
        self.assertIn('Deployment not configured - missing deployment.yml or deployment.yaml file', out)

    def test_functional_structure_is_copied(self):
        """Verify that the structure is copied, and the files are rendered using JINJA2"""

        # prepare configuration
        self.prepare_valid_deployment_yml()
        task = UpdateFilesTask()

        # mock external dependencies: github.com and ansible-galaxy
        task.download_roles = lambda *args, **kwargs: None

        with self.subTest('Verify overall task exit code'):
            out = self.execute_task(task, args={
                '--ask-vault-pass': False,
                '--vault-passwords': '',
                '--ask-ssh-login': False,
                '--ask-ssh-pass': False,
                '--ask-ssh-key-path': False,
                '--ask-sudo-pass': False
            }, env={})
            self.assertIn('TASK_EXIT_RESULT=True', out)

        with self.subTest('Verify copied files'):
            # check a few files, including files that are rendered from JINJA2 like inventory and playbook
            for filename in ['ansible.cfg', 'Vagrantfile', 'harbor.inventory.cfg', 'harbor.playbook.yml']:
                self.assertTrue(os.path.isfile(self.get_test_env_subdirectory('.rkd/deployment') + '/' + filename))

        with self.subTest('Check if JINJA2 templates are rendered'):
            with open(self.get_test_env_subdirectory('.rkd/deployment') + '/harbor.inventory.cfg', 'r') as f:
                # vagrant is a default value from file created by self.prepare_valid_deployment_yml()
                self.assertIn('ansible_ssh_user=docker', f.read())
