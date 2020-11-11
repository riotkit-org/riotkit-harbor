from typing import Tuple
from typing import List
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.deployment.ssh import SSHTask


class SSHTaskTest(BaseHarborTestClass):
    def _execute_task_and_get_sh_calls_and_output(self, args: dict, mock_exceptions: list = None) -> Tuple[List[str], str]:
        calls = []
        task = SSHTask()
        original_sh = task.sh

        def mocked_sh(*args, **kwargs):
            if mock_exceptions:
                for exc in mock_exceptions:
                    if exc in args[0]:
                        return original_sh(*args, **kwargs)

            calls.append(args[0])

        task.sh = mocked_sh

        out = self.execute_mocked_task_and_get_output(
            task,
            args=args,
            env={}
        )

        return calls, out

    def test_ssh_task_creates_a_valid_ssh_command_without_private_key(self):
        """
        Test that ssh command would be invoked along with sshpass - as there is no private key
        """

        self.prepare_valid_deployment_yml()

        sh_calls, out = self._execute_task_and_get_sh_calls_and_output({
            '--ask-vault-pass': False,
            '--vault-passwords': '',
            '--ask-ssh-login': False,
            '--ask-ssh-pass': False,
            '--ask-ssh-key-path': False,
            '--ask-sudo-pass': False,
            '--group': 'production',
            '--num': '0',
            '--print-password': False
        })

        self.assertEqual(['sshpass -p "docker" ssh docker@127.0.0.1 -p 2222'], sh_calls)

    def test_ssh_task_includes_private_key_if_present(self):
        """
        Test that private key, encoded inline will be correctly handled
        """

        self.prepare_valid_deployment_yml_with_private_key()

        sh_calls, out = self._execute_task_and_get_sh_calls_and_output({
            '--ask-vault-pass': False,
            '--vault-passwords': '',
            '--ask-ssh-login': False,
            '--ask-ssh-pass': False,
            '--ask-ssh-key-path': False,
            '--ask-sudo-pass': False,
            '--group': 'production',
            '--num': '0',
            '--print-password': False
        })

        self.assertIn('ssh docker@127.0.0.1 -p 2222 -i /', str(sh_calls))
        self.assertIn('current_test_env/.rkd/.tmp-', str(sh_calls))

    def test_ssh_prints_password_if_sudo_password_is_given(self):
        """
        Test that SUDO password will be print if specified

        See prepare_valid_deployment_yml_with_private_key() for data example
        """

        self.prepare_valid_deployment_yml_with_private_key()

        sh_calls, out = self._execute_task_and_get_sh_calls_and_output({
            '--ask-vault-pass': False,
            '--vault-passwords': '',
            '--ask-ssh-login': False,
            '--ask-ssh-pass': False,
            '--ask-ssh-key-path': False,
            '--ask-sudo-pass': False,
            '--group': 'production',
            '--num': '0',
            '--print-password': True
        })

        self.assertIn('SUDO password is: "sudo-docker"', out)

    def test_ssh_prints_user_password_if_sudo_not_present(self):
        """
        Test that SSH user password will be printed if "sudo_password" not present

        See prepare_valid_deployment_yml() for details
        """

        self.prepare_valid_deployment_yml()

        sh_calls, out = self._execute_task_and_get_sh_calls_and_output({
            '--ask-vault-pass': False,
            '--vault-passwords': '',
            '--ask-ssh-login': False,
            '--ask-ssh-pass': False,
            '--ask-ssh-key-path': False,
            '--ask-sudo-pass': False,
            '--group': 'production',
            '--num': '0',
            '--print-password': True
        })

        self.assertIn('User password is: "docker"', out)

    def test_ssh_decrypts_yaml_when_encoded(self):
        """
        Test that SSH user password will be printed if "sudo_password" not present

        See prepare_valid_deployment_yml() for details
        """

        # do not mock specific sh() calls, so the workflow could be preserved
        mock_exceptions = ['cp deployment.yml', ':harbor:vault:encrypt']

        self.prepare_valid_deployment_yml_encrypted_with_password_test()

        sh_calls, out = self._execute_task_and_get_sh_calls_and_output({
            '--ask-vault-pass': False,
            '--vault-passwords': 'test',
            '--ask-ssh-login': False,
            '--ask-ssh-pass': False,
            '--ask-ssh-key-path': False,
            '--ask-sudo-pass': False,
            '--group': 'production',
            '--num': '0',
            '--print-password': True
        }, mock_exceptions=mock_exceptions)

        self.assertIn('User password is: "docker"', out)
