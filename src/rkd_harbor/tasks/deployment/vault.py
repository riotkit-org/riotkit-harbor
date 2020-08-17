import subprocess
from typing import Dict
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from ...formatting import development_formatting
from .base import BaseDeploymentTask


class EditVaultTask(BaseDeploymentTask):
    """Edits an encrypted file

Example usage:
    # edit ".env-prod" file
    harbor :vault:edit .env-prod --vault-passwords="./.vault-password"

    # usage of environment variable (NOTICE: paths to password files must begin with "/" or "./")
    VAULT_PASSWORDS="./.vault-password-file||second-some-plaintext-password-there" harbor :vault:edit .env-prod

    # use a different text editor (you can also put EDITOR variable to your .env file)
    EDITOR=vim harbor :vault:edit deployment.yml

HINT: You can avoid writing the path in commandline each time by putting `VAULT_PASSWORDS=./path-to-password-file.txt` to the .env file
HINT: You can store vault password file on encrypted flash drive, and make a symbolic link. Every time when you mount an encrypted drive you will gain access to the project
NOTICE: When at least one of vault password files does not exist, then there will be a password prompt
"""

    def get_group_name(self) -> str:
        return ':harbor:vault'

    def get_name(self) -> str:
        return ':edit'

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super(BaseDeploymentTask, self).get_declared_envs()
        envs['VAULT_PASSWORDS'] = ''

        return envs

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('filename', help='Filename')
        self._add_vault_arguments_to_argparse(parser)

    def run(self, context: ExecutionContext) -> bool:
        vault_opts = self._get_vault_opts(context)
        filename = context.get_arg('filename')

        subprocess.check_call('ansible-vault edit %s %s' % (vault_opts, filename), shell=True)

        return True


class EncryptVaultTask(BaseDeploymentTask):
    """Encrypts/Decrypts a file using strong AES-256 algorithm,
output files are suitable to be kept in GIT repository

See the documentation for :harbor:vault:edit task for general file encryption documentation
"""

    def get_group_name(self) -> str:
        return ':harbor:vault'

    def get_name(self) -> str:
        return ':encrypt'

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super(BaseDeploymentTask, self).get_declared_envs()
        envs['VAULT_PASSWORDS'] = ''

        return envs

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--decrypt', '-d', action='store_true', help='Decrypt instead of encrypting')
        parser.add_argument('filename', help='Filename')
        self._add_vault_arguments_to_argparse(parser)

    def run(self, context: ExecutionContext) -> bool:
        vault_opts = self._get_vault_opts(context)
        filename = context.get_arg('filename')
        mode = 'decrypt' if context.get_arg('--decrypt') else 'encrypt'

        self.sh('ansible-vault %s %s %s' % (mode, vault_opts, filename), capture=False)

        return True


class EnvEncryptTask(BaseDeploymentTask):
    """Manages the encryption of .env-prod file

The .env-prod file is a file that could be kept securely in GIT repository while containing passwords
required for services to work.
"""

    def get_group_name(self) -> str:
        return ':harbor:env'

    def get_name(self) -> str:
        return ':encrypt'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super(BaseDeploymentTask, self).get_declared_envs()
        envs['VAULT_PASSWORDS'] = ''

        return envs

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--decrypt', '-d', action='store_true', help='Decrypt instead of encrypting')
        self._add_vault_arguments_to_argparse(parser)

    def run(self, context: ExecutionContext) -> bool:
        vault_opts = self._get_vault_opts(context)
        mode = 'decrypt' if context.get_arg('--decrypt') else 'encrypt'

        src = '.env'
        dst = '.env-prod'

        if mode == 'decrypt':
            src = '.env-prod'
            dst = '.env'

        self.sh('cp %s %s-tmp' % (src, dst))
        self.sh('ansible-vault %s %s %s-tmp' % (mode, vault_opts, dst), capture=False)
        self.sh('mv %s-tmp %s' % (dst, dst))

        if mode == 'encrypt':
            try:
                self.sh('git add %s' % dst)
            except:
                pass

        return True
