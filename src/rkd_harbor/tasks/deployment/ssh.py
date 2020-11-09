from typing import Dict
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from ...formatting import development_formatting
from ...exception import MissingDeploymentConfigurationError
from .base import BaseDeploymentTask


class SSHTask(BaseDeploymentTask):
    """SSH into a host defined in a deployment configuration"""

    def get_name(self) -> str:
        return ':ssh'

    def get_group_name(self) -> str:
        return ':harbor:deployment'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def configure_argparse(self, parser: ArgumentParser):
        self._add_ask_pass_arguments_to_argparse(parser)
        self._add_vault_arguments_to_argparse(parser)

        parser.add_argument('--group', help='Node group eg. "production"', required=True)
        parser.add_argument('--num', help='Node number from given group, defaults to "0"', default="0")
        parser.add_argument('--print-password', help='Print user password', action='store_true')

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super().get_declared_envs()
        envs['VAULT_PASSWORDS'] = ''

        return envs

    def run(self, context: ExecutionContext) -> bool:
        self._preserve_vault_parameters_for_usage_in_inner_tasks(context)

        node_group = context.get_arg('--group')
        node_num = int(context.get_arg('--num'))
        should_print_password = context.get_arg('--print-password')

        try:
            config = self.get_config()

            if not self._validate(node_group, node_num, config):
                return False

            if should_print_password:
                self._print_password(node)

            return self._ssh(node)

        except MissingDeploymentConfigurationError as e:
            self.io().error_msg(str(e))
            return False

    def _validate(self, node_group: str, node_num: int, config: dict):
        if node_group not in config['nodes'].keys():
            self.io().error_msg('Node group "{}" not found'.format(node_group))
            return False

        try:
            node = config['nodes'][node_group][node_num]
        except KeyError:
            self.io().error_msg('Node group "{}" does not have node of number #{}'.format(node_group, node_num))
            return False

    def _print_password(self, node: dict):
        if 'sudo_password' in node:
            self.io().info_msg('>> SUDO password is: "{}"'.format(node['sudo_password']))
            return

        if 'password' in node:
            self.io().info_msg('>> User password is: "{}"'.format(node['password']))
            return

    def _ssh(self, node: dict) -> bool:
        ssh_cmd = 'ssh {}@{} -p {}'.format(node['user'], node['host'], node['port'])

        if 'private_key' in node:
            ssh_cmd += ' -i {}'.format(node['private_key'])

        self.sh(ssh_cmd)

        return True
