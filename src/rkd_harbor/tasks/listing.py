from typing import Dict
from argparse import ArgumentParser
from tabulate import tabulate
from rkd.api.contract import ExecutionContext
from .base import BaseProfileSupportingTask
from ..service import ServiceDeclaration


class ListDefinedServices(BaseProfileSupportingTask):
    """Lists all defined containers in YAML files (can be limited by --profile selector)"""

    def get_group_name(self) -> str:
        return ':harbor:service'

    def get_name(self) -> str:
        return ':list'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--group-by', '-g', help='Group list by: url, none. Default: none', default='none')

    def run(self, ctx: ExecutionContext) -> bool:
        group_by = ctx.get_arg('--group-by')
        services = self.get_matching_services(ctx)

        # table
        table_headers = ['Priority', 'Name', 'Declared version', 'Replicas', 'URL', 'Ports',
                         'Maintenance mode', 'Update strategy', 'Watchtower']
        table_body = []

        running = self.containers(ctx).get_created_containers(only_running=True)

        for service in services:
            domains = service.get_domains()

            # GROUP-BY: list per-domain
            if group_by == 'url':
                for domain in domains:
                    self._append_to_table(table_body, service, running, domain)

                # list also services that are not under a domain (internal services or exposed via ports)
                if not domains:
                    self._append_to_table(table_body, service, running, domain='-')

            # GROUP-BY: none
            if group_by == 'none':
                self._append_to_table(table_body, service, running, domain=self._format_domains(domains))

        self.io().outln(tabulate(table_body, headers=table_headers))

        return True

    @staticmethod
    def _format_domains(domains: list):
        return "\n".join(domains)

    @staticmethod
    def _append_to_table(table_body: list, service: ServiceDeclaration,
                         running_services: Dict[str, Dict[int, bool]], domain: str):

        is_running = service.get_name() in running_services
        replicas_running = ' [%i/%i]' % (
            len(running_services[service.get_name()]) if is_running else 0,
            service.get_desired_replicas_count()
        )

        table_body.append([
            service.get_priority_number(),
            service.get_name(),
            service.get_declared_version(),
            replicas_running,
            domain,
            "\n".join(service.get_ports()),
            bool2str(service.is_using_maintenance_mode(), y='Available', n='N/A'),
            service.get_update_strategy(),
            bool2str(service.is_using_watchtower())
        ])


def bool2str(val: bool, y: str = 'Active', n: str = 'Not active'):
    return y if val else n
