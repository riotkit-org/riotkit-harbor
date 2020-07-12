import subprocess
from harbor.test import BaseHarborTestClass
from harbor.tasks.deployment import DeploymentTask
from harbor.tasks.deployment import UpdateFilesTask


class DeploymentTaskTask(BaseHarborTestClass):
    def test_functional_validates_if_structure_exists(self):
        """Verify that :deployment:apply requires :deployment:files:update to be called first
        """

        out = self.execute_task(DeploymentTask(),
                                args={'--playbook': 'harbor.playbook.yml',
                                      '--inventory': 'harbor.inventory.yml',
                                      '--git-key': '',
                                      '--branch': 'master',
                                      '--profile': '',
                                      '--debug': False,
                                      '--vault-passwords': '',
                                      '--ask-vault-pass': False},
                                env={})

        self.assertIn('Deployment not configured. Use `harbor :deployment:role:update` first', out)
        self.assertIn('TASK_EXIT_RESULT=False', out)

    # todo: Move test to other class
    def test_functional_validates_deployment_yml_file_not_created(self):
        """Test that deployment.yml/deployment.yaml needs to be created first and the message for the end user is clear
        """

        out = self.execute_task(UpdateFilesTask(),
                                args={
                                    '--ask-vault-pass': False,
                                    '--vault-passwords': ''
                                },
                                env={})

        self.assertIn('Deployment not configured - missing deployment.yml or deployment.yaml file', out)

    def test_functional_passes_structure_validation_after_using_update_command(self):
        """Verify that when :deployment:files:update is called, then :deployment:apply, then the validation
        in :deployment:apply is passing - as the files are created by first task
        """

        self._prepare_valid_configuration()
        ansible_call = []

        deployment_task = DeploymentTask()
        deployment_task.spawn_ansible = lambda *args, **kwargs: ansible_call.append(args)

        self.execute_task(deployment_task,
                          args={'--playbook': 'harbor.playbook.yml',
                                '--inventory': 'harbor.inventory.yml',
                                '--git-key': '',
                                '--branch': 'master',
                                '--profile': '',
                                '--debug': False,
                                '--vault-passwords': '',
                                '--ask-vault-pass': False},
                          env={})

        self.assertIn('ansible-playbook', ansible_call[0][0])
        self.assertIn('./harbor.playbook.yml', ansible_call[0][0])
        self.assertIn('-i harbor.inventory.yml', ansible_call[0][0])
        self.assertIn('-e git_branch="master"', ansible_call[0][0])
        self.assertIn('-e harbor_deployment_profile=""', ansible_call[0][0])

    def test_functional_decrypts_encrypted_deployment_yml_file_on_startup(self):
        """Check that deployment.yml file can be encrypted, and that given vault password in commandline will allow
        to decrypt the contents automatically"""

        self._prepare_valid_configuration()
        ansible_call = []
        passphrase_file_path = self.get_test_env_subdirectory('.rkd') + '/tmp-secret.txt'

        # 1) Write test password
        with open(passphrase_file_path, 'w') as f:
            f.write('International-Workers-Association')

        # 2) Encrypt a file
        deployment_yml_path = self.get_test_env_subdirectory('') + '/deployment.yml'
        subprocess.check_call(
            ['ansible-vault encrypt --vault-password-file=%s %s' % (passphrase_file_path, deployment_yml_path)],
            shell=True)

        # 3) Run a deployment while the deployment.yml is encrypted
        deployment_task = DeploymentTask()
        deployment_task.spawn_ansible = lambda *args, **kwargs: ansible_call.append(args)

        out = self.execute_task(deployment_task,
                                args={'--playbook': 'harbor.playbook.yml',
                                      '--inventory': 'harbor.inventory.yml',
                                      '--git-key': '',
                                      '--branch': 'master',
                                      '--profile': '',
                                      '--debug': False,
                                      '--vault-passwords': passphrase_file_path,
                                      '--ask-vault-pass': False},
                                env={})

        self.assertIn('--vault-password-file=', ansible_call[0][0])
        self.assertIn('.rkd/tmp-secret.txt', ansible_call[0][0])
        self.assertIn('TASK_EXIT_RESULT=True', out)

    def _prepare_valid_configuration(self):
        """Internal: Prepares a valid deployment.yml and already synchronized files structure, downloaded role"""

        with open(self.get_test_env_subdirectory('') + '/deployment.yml', 'w') as f:
            f.write('''deploy_user: vagrant
deploy_group: vagrant
remote_dir: /project
git_url: https://github.com/riotkit-org/empty
git_secret_url: https://github.com/riotkit-org/empty
configure_sudoers: no

nodes:
    production:
        # example configuration for testing environment based on Vagrant
        # to run the environment type: harbor :deployment:vagrant -c "up --provision"
        - host: 127.0.0.1
          port: 2222
          user: docker
          password: docker
''')

        self.execute_task(UpdateFilesTask(),
                          args={
                              '--ask-vault-pass': False,
                              '--vault-passwords': ''
                          },
                          env={})
