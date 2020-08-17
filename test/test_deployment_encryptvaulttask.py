from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.deployment.vault import EncryptVaultTask


class EncryptVaultTaskTest(BaseHarborTestClass):
    def test_functional_file_is_encrypted(self):
        """Test encryption"""

        with self.subTest('Encrypt the file'):
            self.execute_task(EncryptVaultTask(),
                              args={
                                  '--ask-vault-pass': False,
                                  '--vault-passwords': 'InternalWorkersAssociation',
                                  '--decrypt': False,
                                  'filename': 'README.md'
                              },
                              env={})

            with open(self.get_test_env_subdirectory('') + '/README.md', 'rb') as f:
                self.assertIn('$ANSIBLE_VAULT;', f.read().decode('utf-8'))

        with self.subTest('Decrypt the file'):
            self.execute_task(EncryptVaultTask(),
                              args={
                                  '--ask-vault-pass': False,
                                  '--vault-passwords': 'InternalWorkersAssociation',
                                  '--decrypt': True,
                                  'filename': 'README.md'
                              },
                              env={})

            with open(self.get_test_env_subdirectory('') + '/README.md', 'rb') as f:
                self.assertNotIn('$ANSIBLE_VAULT;', f.read().decode('utf-8'))
