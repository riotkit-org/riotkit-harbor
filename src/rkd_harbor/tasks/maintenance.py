import os
from typing import List
from argparse import ArgumentParser
from abc import abstractmethod
from rkd.api.contract import ExecutionContext
from .base import HarborBaseTask
from ..formatting import prod_formatting
from ..exception import ServiceNotFoundInYamlLookedByCriteria
from ..exception import ServiceNotFoundInYaml


class BaseMaintenanceManagementTask(HarborBaseTask):
    def get_group_name(self) -> str:
        return ':harbor:maintenance'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--domain', '-d', help='Domain name', default='')
        parser.add_argument('--service', '-s', help='Service name', default='')
        parser.add_argument('--global', '-g', help='Set maintenance for all domains', action='store_true')

    def run(self, context: ExecutionContext) -> bool:
        """Validate parameters and select action"""

        is_global = context.get_arg('--global')
        domain = context.get_arg('--domain')
        service = context.get_arg('--service')

        directory = self.get_data_path(context) + '/maintenance-mode'

        if not self._validate_switches(is_global, domain, service):
            self.io().error_msg('Cannot use together --global, --domain and --service switch. Pick one of them.')
            return False

        try:
            if is_global:
                return self.act([directory + '/on'], 'globally')

            elif service:
                return self.act_for_service(directory, service, context)

            elif domain:
                return self.act_for_domain(directory, domain, context)
            else:
                self.io().error_msg('Must specify --global or --domain switch')
                return False

        except PermissionError as e:
            self.io().error_msg('No write permissions. Set permissions or use sudo? %s' % str(e))
            return False

    def act_for_service(self, directory: str, service: str, ctx: ExecutionContext):
        try:
            domains = self.services(ctx).get_by_name(service).get_domains()

        except ServiceNotFoundInYaml:
            self.io().error_msg('Service "%s" was not defined' % service)
            return False

        return self.act(
            list(map(lambda domain: directory + '/%s-on' % domain, domains)),
            'for service "%s"' % service
        )

    def act_for_domain(self, directory, domain, context):
        try:
            self.services(context).find_by_domain(domain)
        except ServiceNotFoundInYamlLookedByCriteria:
            self.io().error_msg('Domain is not valid')
            return False

        return self.act([directory + '/%s-on' % domain], 'for domain "%s"' % domain)

    @abstractmethod
    def act(self, paths: List[str], subject: str) -> bool:
        pass

    def format_task_name(self, name) -> str:
        return prod_formatting(name)

    @staticmethod
    def _validate_switches(is_global, domain, service):
        switches = 0

        if is_global:
            switches += 1

        if domain:
            switches += 1

        if service:
            switches += 1

        return switches == 1


class MaintenanceOnTask(BaseMaintenanceManagementTask):
    """Turn on the maintenance mode"""

    def get_name(self) -> str:
        return ':on'

    def act(self, paths: List[str], subject: str) -> bool:
        for path in paths:
            with open(path, 'w') as f:
                f.write('We are on strike ;)')

            os.chmod(path, 0o777)

        self.io().success_msg('Maintenance mode %s is on' % subject)

        return True


class MaintenanceOffTask(BaseMaintenanceManagementTask):
    """Turn on the maintenance mode"""

    def get_name(self) -> str:
        return ':off'

    def act(self, paths: List[str], subject: str) -> bool:
        for path in paths:
            if os.path.isfile(path):
                os.unlink(path)

        self.io().success_msg('Maintenance mode %s is off' % subject)

        return True


class MaintenanceListTask:
    pass
