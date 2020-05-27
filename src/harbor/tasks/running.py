from abc import ABC
from argparse import ArgumentParser
from typing import List
from tabulate import tabulate
from rkd.contract import ExecutionContext
from .base import HarborBaseTask
from ..service import Service


class ListContainersTask(HarborBaseTask):
    """List all containers
    """

    def get_name(self) -> str:
        return ':ps'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--quiet', '-q', help='Only display IDs', action='store_true')
        parser.add_argument('--all', '-a', help='Show all containers, including stopped', action='store_true')

    def run(self, context: ExecutionContext) -> bool:
        params = []

        if context.get_arg('--quiet'):
            params.append('--quiet')

        if context.get_arg('--all'):
            params.append('--all')

        self.compose(['ps'] + params)
        return True


class BaseProfileSupportingTasks(HarborBaseTask, ABC):
    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--profile', '-p', help='Services profile', default='')

    def get_matching_services(self, context: ExecutionContext) -> List[Service]:
        service_selector = self.profile_loader(context).load_profile(context.get_arg('--profile'))
        matched = service_selector.find_matching_services(self.get_services())

        return matched


class StartTask(BaseProfileSupportingTasks):
    """Create and start containers
    """
    
    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--no-recreate', help='If containers already exist, don\'t recreate them. ' +
                                                  'Incompatible with --force-recreate and -V.', action='store_true')
        parser.add_argument('--force-recreate', help='Recreate containers even if their ' +
                                                     'configuration and image haven\'t changed.', action='store_true')
        parser.add_argument('--no-build', help='Don\'t build an image, even if it\'s missing.', action='store_true')
        parser.add_argument('--no-deps', help='Don\'t start linked services.', action='store_true')
        parser.add_argument('--no-detach', '-n', help='Don\'t start in detach mode', action='store_true')

    def get_name(self) -> str:
        return ':start'

    def run(self, context: ExecutionContext) -> bool:
        service_names = []

        for service in self.get_matching_services(context):
            service_names.append(service.get_name())

        self.compose(['up', '-d'] + service_names)

        return True


class ListDefinedServices(BaseProfileSupportingTasks):
    """Lists all defined containers in YAML files (can be limited by --profile selector)"""

    def get_group_name(self) -> str:
        return ':harbor:services'

    def get_name(self) -> str:
        return ':ps'

    def get_running_services(self):
        """Gets all running services"""
        return self.compose(['ps', '--services'], capture=True).strip().split("\n")

    def run(self, context: ExecutionContext) -> bool:
        services = self.get_matching_services(context)
        table_headers = ['Name', 'Running', 'URL', 'Ports', 'Watchtower', 'Maintenance mode']
        table_body = []

        running = self.get_running_services()

        for service in services:
            domains = service.get_domains()
            ports = ', '.join(service.get_ports())
            is_running = bool2str(service.get_name() in running, y='Yes', n='No')

            # list per-domain
            for domain in domains:
                table_body.append([
                    service.get_name(),
                    is_running,
                    domain,
                    ports,
                    bool2str(service.is_using_watchtower()),
                    bool2str(service.is_using_maintenance_mode())
                ])

            # list also services that are not under a domain (internal services or exposed via ports)
            if not domains:
                table_body.append([
                    service.get_name(),
                    is_running,
                    '-',
                    ports,
                    bool2str(service.is_using_watchtower()),
                    bool2str(service.is_using_maintenance_mode())
                ])

        self.io().outln(tabulate(table_body, headers=table_headers))

        return True


def bool2str(val: bool, y: str = 'Active', n: str = 'Not active'):
    return y if val else n
