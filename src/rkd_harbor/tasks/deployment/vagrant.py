import subprocess
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from ...formatting import development_formatting
from .base import BaseDeploymentTask


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

