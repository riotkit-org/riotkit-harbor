from typing import Dict
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from ...formatting import development_formatting
from ...exception import MissingDeploymentConfigurationError
from .base import BaseDeploymentTask


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
        self._add_ask_pass_arguments_to_argparse(parser)
        self._add_vault_arguments_to_argparse(parser)

    def run(self, context: ExecutionContext) -> bool:
        self._preserve_vault_parameters_for_usage_in_inner_tasks(context)

        try:
            return self.install_and_configure_role(context, force_update=True)

        except MissingDeploymentConfigurationError as e:
            self.io().error_msg(str(e))
            return False
