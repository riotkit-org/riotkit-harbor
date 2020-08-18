import os
import subprocess
from typing import Dict
from typing import Tuple
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from ..base import HarborBaseTask
from ...formatting import development_formatting
from ...exception import MissingDeploymentConfigurationError
from .base import BaseDeploymentTask

HARBOR_ROOT = os.path.dirname(os.path.realpath(__file__)) + '/../../deployment/files'


class DeploymentTask(BaseDeploymentTask):
    """Deploys your project from GIT to a PRODUCTION server

All changes needs to be COMMITED and PUSHED to GIT server, the task does not copy local files.

The deployment task can be extended by environment variables and switches to make possible any customizations
such as custom playbook, custom role or a custom inventory. The environment variables from .env are considered.

Example usage:
    # deploy services matching profile "gateway", use password stored in .vault-password for Ansible Vault
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
        self._add_ask_pass_arguments_to_argparse(parser)
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
            self.io().error_msg('Deployment not configured. Use `harbor :deployment:files:update` first')
            return False

        try:
            self.install_and_configure_role(context, force_update=False)

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
        self.io().info('Spawning Ansible, you may be asked for vault password to decrypt .env-prod')
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

