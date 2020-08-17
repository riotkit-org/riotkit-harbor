import subprocess
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.deployment.vault import EnvEncryptTask


class EnvEncryptTaskTest(BaseHarborTestClass):
    def test_functional_env_is_encrypted_then_decrypted(self):
        """Verify that the structure is copied, and the files are rendered using JINJA2"""

        # 1) Encryption
        with self.subTest('Encrypted file ".env-prod" is produced'):
            self.execute_task(EnvEncryptTask(),
                              args={
                                  '--ask-vault-pass': False,
                                  '--vault-passwords': 'union',
                                  '--decrypt': False
                              },
                              env={})

            with open(self.get_test_env_subdirectory('') + '/.env-prod', 'rb') as f:
                self.assertIn('$ANSIBLE_VAULT;', f.read().decode('utf-8'))

        # before next subtest remove the original .env file contents,
        # so we can check if it will be recreated from .env-prod
        subprocess.check_call('echo "" > .env', shell=True)

        # 2) Decryption
        with self.subTest('File ".env" is decrypted back from ".env-prod"'):
            self.execute_task(EnvEncryptTask(),
                              args={
                                  '--ask-vault-pass': False,
                                  '--vault-passwords': 'union',
                                  '--decrypt': True
                              },
                              env={})

            with open(self.get_test_env_subdirectory('') + '/.env', 'rb') as f:
                content = f.read().decode('utf-8')

                self.assertNotIn('$ANSIBLE_VAULT;', content)
                self.assertIn('COMPOSE_PROJECT_NAME=env_simple', content)
