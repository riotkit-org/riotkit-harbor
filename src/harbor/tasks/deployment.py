import os
import subprocess
from uuid import uuid4
from abc import ABC
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import StrictUndefined
from jinja2.exceptions import UndefinedError
from typing import Dict
from typing import Tuple
from argparse import ArgumentParser
from rkd.contract import ExecutionContext
from rkd.yaml_parser import YamlFileLoader
from rkd.exception import MissingInputException
from .base import HarborBaseTask
from ..formatting import development_formatting
from ..exception import MissingDeploymentConfigurationError

HARBOR_ROOT = os.path.dirname(os.path.realpath(__file__)) + '/../deployment/files'


class BaseDeploymentTask(HarborBaseTask, ABC):
    ansible_dir: str = '.rkd/deployment'
    _config: dict
    vault_args: list = []

    def get_config(self) -> dict:
        """Loads and parses deployment.yml file. Supports Ansible Vault encryption"""

        deployment_filenames = ['deployment.yml', 'deployment.yaml']

        try:
            self._config
        except AttributeError:

            # try multiple files
            for filename in deployment_filenames:
                if os.path.isfile(filename):

                    #
                    # Check file contents before
                    #
                    with open(filename, 'rb') as f:
                        content = f.read().decode('utf-8')
                        #
                        # When file is encrypted, then decrypt it
                        #
                        if content.startswith('$ANSIBLE_VAULT;'):
                            tmp_vault_filename = '.tmp-' + str(uuid4())
                            tmp_vault_path = './.rkd/' + tmp_vault_filename

                            self.sh('cp %s %s' % (filename, tmp_vault_path))
                            self.rkd([':harbor:vault:encrypt', '-d', tmp_vault_path] + self.vault_args)

                            try:
                                self._config = YamlFileLoader(self._ctx.directories).load_from_file(
                                    tmp_vault_filename,
                                    'org.riotkit.harbor/deployment/v1'
                                )
                            finally:
                                self.sh('rm -f %s' % tmp_vault_path)

                            return self._config

                    self._config = YamlFileLoader(self._ctx.directories).load_from_file(
                        filename,
                        'org.riotkit.harbor/deployment/v1'
                    )

                    return self._config

            raise MissingDeploymentConfigurationError()

        return self._config

    def _verify_synced_version(self, abs_ansible_dir: str):
        """Verifies last synchronization - displays warning if Harbor version was changed after last
        files synchronization"""

        if not os.path.isfile(abs_ansible_dir + '/.synced'):
            return

        with open(abs_ansible_dir + '/.synced', 'rb') as f:
            synced_version = f.read().decode('utf-8').strip()
            actual_version = self.get_harbor_version()

            if synced_version != actual_version:
                self.io().warn('Ansible deployment in .rkd/deployment is not up-to-date. We recommend to update' +
                               ' from %s to %s' % (synced_version, actual_version))

    def _write_synced_version(self, abs_ansible_dir: str):
        """Writes information about, in which Harbor version the files were synced last time"""

        with open(abs_ansible_dir + '/.synced', 'wb') as f:
            f.write(self.get_harbor_version().encode('utf-8'))

    def role_is_installed_and_configured(self) -> bool:
        return os.path.isfile(self.ansible_dir + '/.synced')

    def install_and_configure_role(self, force_update: bool = False) -> bool:
        """Install an Ansible role from galaxy, and configure playbook, inventory, all the needed things"""

        abs_ansible_dir = os.path.realpath(self.ansible_dir)
        should_update = force_update or not os.path.isfile(abs_ansible_dir + '/.synced')

        self.io().info('Checking role installation...')
        self._silent_mkdir(abs_ansible_dir)
        self._verify_synced_version(abs_ansible_dir)

        if not self._synchronize_structure_from_template(abs_ansible_dir, only_jinja_templates=True):
            self.io().error_msg('Cannot synchronize templates')
            return False

        if should_update:
            self.io().info('Role will be updated')

            if not self._synchronize_structure_from_template(abs_ansible_dir):
                self.io().error_msg('Cannot synchronize structure')
                return False

            self.io().debug('Downloading fresh role...')
            self.download_roles()

            self._write_synced_version(abs_ansible_dir)

        return True

    def download_roles(self):
        self.sh(' '.join([
            'ansible-galaxy',
            'install', '-r', self.ansible_dir + '/requirements.yml',
            '-p', self.ansible_dir + '/roles/',
            '--force'
        ]), capture=False)

    def _synchronize_structure_from_template(self, abs_ansible_dir: str, only_jinja_templates: bool = False) -> bool:
        """Synchronizes template structure into .rkd/deployment"""

        self.io().debug(
            'Synchronizing structure from template (only_jinja_templates=' + str(only_jinja_templates) + ')')

        # synchronize directory structure
        for root, subdirs, files in os.walk(HARBOR_ROOT):
            relative_root = root[len(HARBOR_ROOT) + 1:]

            self._silent_mkdir(abs_ansible_dir + '/' + relative_root)

            for file in files:
                if only_jinja_templates and not file.endswith('.j2'):
                    continue

                abs_src_file_path = root + '/' + file
                abs_dest_file_path = abs_ansible_dir + '/' + relative_root + '/' + file

                if not self._copy_file(abs_src_file_path, abs_dest_file_path):
                    self.io().error('Cannot process file %s' % abs_dest_file_path)
                    return False

        return True

    def _copy_file(self, abs_src_file_path: str, abs_dest_file_path: str):
        """Copies a file from template directory - supports jinja2 files rendering on-the-fly"""

        if abs_dest_file_path.endswith('.j2'):
            abs_dest_file_path = abs_dest_file_path[:-3]

            with open(abs_src_file_path, 'rb') as f:
                tpl = Environment(loader=FileSystemLoader(['./', './rkd/deployment']), undefined=StrictUndefined)\
                        .from_string(f.read().decode('utf-8'))

            try:
                variables = self._prepare_variables()

                with open(abs_dest_file_path, 'wb') as f:
                    f.write(tpl.render(**variables).encode('utf-8'))

            except UndefinedError as e:
                self.io().error(str(e) + " - required in " + abs_src_file_path + ", please define it in deployment.yml")
                return False

            return True

        subprocess.check_call(['cp', '-p', abs_src_file_path, abs_dest_file_path])
        self.io().debug('Created ' + abs_dest_file_path)
        return True

    def _prepare_variables(self):
        """Glues together variables from environment and from deployment.yaml for exposing in JINJA2 templates"""

        variables = {}
        variables.update(os.environ)
        variables.update(self.get_config())

        if 'git_url' not in variables:
            variables['git_url'] = subprocess\
                .check_output(['git', 'config', '--get', 'remote.origin.url']).decode('utf-8')\
                .replace('\n', '')\
                .strip()

        if 'git_secret_url' not in variables:
            variables['git_secret_url'] = variables['git_url'].replace('\n', '')

        return variables

    def _preserve_vault_parameters_for_usage_in_inner_tasks(self, ctx: ExecutionContext):
        """Preserve original parameters related to Vault, so those parameters can be propagated to inner tasks"""

        try:
            vault_passwords = ctx.get_arg_or_env('--vault-passwords')
        except MissingInputException:
            vault_passwords = ''

        # keep the vault arguments for decryption of deployment.yml
        self.vault_args = ['--vault-passwords=' + vault_passwords]
        if ctx.get_arg('--ask-vault-pass'):
            self.vault_args += '--ask-vault-pass'

    def _get_vault_opts(self, ctx: ExecutionContext, chdir: str = '') -> str:
        """Creates options to pass in Ansible Vault commandline"""

        try:
            vault_passwords = ctx.get_arg_or_env('--vault-passwords').split('||')
        except MissingInputException:
            vault_passwords = []

        num = 0
        opts = ''
        enforce_ask_pass = ctx.get_arg('--ask-vault-pass')

        for passwd in vault_passwords:
            num = num + 1

            if not passwd:
                continue

            if passwd.startswith('./') or passwd.startswith('/'):
                if os.path.isfile(passwd):
                    opts += ' --vault-password-file="%s" ' % (chdir + passwd)
                else:
                    self.io().error('Vault password file "%s" does not exist, calling --ask-vault-pass' % passwd)
                    enforce_ask_pass = True
            else:
                tmp_vault_file = './.rkd/.tmp-vault-' + str(uuid4())

                with open(tmp_vault_file, 'w') as f:
                    f.write(passwd)

                opts += ' --vault-password-file="%s" ' % (chdir + tmp_vault_file)

        if enforce_ask_pass:
            opts += ' --ask-vault-pass '

        return opts

    def _clear_old_vault_temporary_files(self):
        self.sh('rm -f ./.rkd/.tmp-vault*', capture=True)

    @classmethod
    def _add_vault_arguments_to_argparse(cls, parser: ArgumentParser):
        parser.add_argument('--ask-vault-pass', '-v', help='Ask for vault password interactively')
        parser.add_argument('--vault-passwords', '-V', help='Vault passwords separated by "||" eg. 123||456')


class UpdateFilesTask(BaseDeploymentTask):
    """Updates an Ansible role and required configuration files.
    Warning: Overwrites existing files, but does not remove custom files in '.rkd/deployment' directory"""

    def get_name(self) -> str:
        return ':update'

    def get_group_name(self) -> str:
        return ':harbor:deployment:files'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super(BaseDeploymentTask, self).get_declared_envs()
        envs['VAULT_PASSWORDS'] = ''

        return envs

    def configure_argparse(self, parser: ArgumentParser):
        self._add_vault_arguments_to_argparse(parser)

    def run(self, context: ExecutionContext) -> bool:
        self._preserve_vault_parameters_for_usage_in_inner_tasks(context)

        try:
            return self.install_and_configure_role(force_update=True)

        except MissingDeploymentConfigurationError as e:
            self.io().error_msg(str(e))
            return False


class DeploymentTask(BaseDeploymentTask):
    """Deploys your project from GIT to a PRODUCTION server

All changes needs to be COMMITED and PUSHED to GIT server, the task does not copy local files.

The deployment task can be extended by environment variables and switches to make possible any customizations
such as custom playbook, custom role or a custom inventory. The environment variables from .env are considered.

Example usage:
    # deploy services matching profile "gateway", use password stored in .vault-apssword for Ansible Vault
    harbor :deployment:apply -V .vault-password --profile=gateway

    # another example with Vault, multiple passwords, and environment variable usage
    # (NOTICE: paths to password files must begin with "/" or "./")
    VAULT_PASSWORDS="./.vault-password-file||other-plain-text-password" harbor :deployment:apply

    # deploy from different branch
    harbor :deployment:apply --branch production_fix_1

    # use SSH-AGENT & key-based authentication by specifying path to private key
    harbor :deployment:apply --git-key=~/.ssh/id_rsa
    """

    def get_name(self) -> str:
        return ':apply'

    def get_group_name(self) -> str:
        return ':harbor:deployment'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super(DeploymentTask, self).get_declared_envs()
        envs['PLAYBOOK'] = 'harbor.playbook.yml'
        envs['INVENTORY'] = 'harbor.inventory.cfg'
        envs['GIT_KEY'] = ''
        envs['VAULT_PASSWORDS'] = ''

        return envs

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--playbook', '-p', help='Playbook name', default='harbor.playbook.yml')
        parser.add_argument('--git-key', '-k', help='Path to private key for a git repository eg. ~/.ssh/id_rsa',
                            default='')
        parser.add_argument('--inventory', '-i', help='Inventory filename', default='harbor.inventory.cfg')
        parser.add_argument('--debug', '-d', action='store_true', help='Set increased logging for Ansible output')
        parser.add_argument('--branch', '-b', help='Git branch to deploy from', default='master')
        parser.add_argument('--profile', help='Harbor profile to filter out services that needs to be deployed',
                            default='')
        self._add_vault_arguments_to_argparse(parser)

    def run(self, context: ExecutionContext) -> bool:
        playbook_name = context.get_arg_or_env('--playbook')
        inventory_name = context.get_arg_or_env('--inventory')
        git_private_key_path = context.get_arg_or_env('--git-key')
        branch = context.get_arg('--branch')
        profile = context.get_arg('--profile')
        debug = context.get_arg('--debug')

        # keep the vault arguments for decryption of deployment.yml
        self._preserve_vault_parameters_for_usage_in_inner_tasks(context)

        if not self.role_is_installed_and_configured():
            self.io().error_msg('Deployment not configured. Use `harbor :deployment:role:update` first')
            return False

        try:
            self.install_and_configure_role(force_update=False)

        except MissingDeploymentConfigurationError as e:
            self.io().error_msg(str(e))
            return False

        pwd_backup = os.getcwd()
        pid = None

        try:
            command = ''
            opts = ''

            if git_private_key_path:
                sock, pid = self.spawn_ssh_agent()
                command += 'export SSH_AUTH_SOCK=%s; export SSH_AGENT_PID=%i; ssh-add %s; sleep 5; ' % \
                           (sock, pid, git_private_key_path)

            if debug:
                opts += ' -vv '

            opts += ' -e git_branch="%s" ' % branch
            opts += ' -e harbor_deployment_profile="%s" ' % profile
            opts += self._get_vault_opts(context, '../../')

            os.chdir(self.ansible_dir)
            command += 'ansible-playbook ./%s -i %s %s' % (
                playbook_name,
                inventory_name,
                opts
            )

            self.spawn_ansible(command)
        finally:
            os.chdir(pwd_backup)

            if pid:
                self.kill_ssh_agent(pid)

        return True

    def spawn_ansible(self, command):
        self.io().info('Spawning Ansible')
        return self.sh(command)

    def spawn_ssh_agent(self) -> Tuple[str, int]:
        out = subprocess.check_output('eval $(ssh-agent -s);echo "|${SSH_AUTH_SOCK}|${SSH_AGENT_PID}";', shell=True).decode('utf-8')
        parts = out.split('|')
        sock = parts[1]
        pid = int(parts[2].strip())

        self.io().debug('Spawned ssh-agent - sock=%s, pid=%i' % (sock, pid))

        return sock, pid

    def kill_ssh_agent(self, pid: int):
        self.io().debug('Clean up - killing ssh-agent at PID=%i' % pid)
        subprocess.check_call(['kill', str(pid)])


class CreateExampleDeploymentFileTask(HarborBaseTask):
    """Creates a example deployment.yml file"""

    def get_group_name(self) -> str:
        return ':harbor:deployment'

    def get_name(self) -> str:
        return ':create-example'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def run(self, context: ExecutionContext) -> bool:
        if os.path.isfile('./deployment.yml') or os.path.isfile('./deployment.yaml'):
            self.io().error_msg('deployment.yml or deployment.yaml already exists')
            return False

        subprocess.check_call(['cp', HARBOR_ROOT + '/../examples/deployment.yml', './deployment.yml'])
        self.io().success_msg('File "deployment.yml" created.')
        self.io().print_line()
        self.io().info_msg('The example is initially adjusted to work with Vagrant test virtual machine.')
        self.io().info_msg(' - `harbor :deployment:vagrant -c "up --provision"` to bring machine up')
        self.io().info_msg(' - `harbor :deployment:apply --git-key=~/.ssh/id_rsa` to perform a test deployment')

        return True


class ManageVagrantTask(BaseDeploymentTask):
    """Controls a test virtual machine using Vagrant"""

    def get_group_name(self) -> str:
        return ':harbor:deployment'

    def get_name(self) -> str:
        return ':vagrant'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--cmd', '-c', required=True, help='Vagrant commandline')

    def run(self, context: ExecutionContext) -> bool:
        cmd = context.get_arg('--cmd')

        try:
            subprocess.check_call('cd %s && vagrant %s' % (self.ansible_dir, cmd), shell=True)

        except subprocess.CalledProcessError:
            return False

        return True


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

        try:
            subprocess.check_call('ansible-vault edit %s %s' % (vault_opts, filename), shell=True)
        finally:
            self._clear_old_vault_temporary_files()

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

        try:
            self.sh('ansible-vault %s %s %s' % (mode, vault_opts, filename), capture=False)
        finally:
            self._clear_old_vault_temporary_files()

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

        try:
            self.sh('cp %s %s-tmp' % (src, dst))
            self.sh('ansible-vault %s %s %s-tmp' % (mode, vault_opts, dst), capture=False)
            self.sh('mv %s-tmp %s' % (dst, dst))
        finally:
            self._clear_old_vault_temporary_files()

        if mode == 'encrypt':
            try:
                self.sh('git add %s' % dst)
            except:
                pass

        return True
