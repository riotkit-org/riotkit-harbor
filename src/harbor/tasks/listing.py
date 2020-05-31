from tabulate import tabulate
from rkd.contract import ExecutionContext
from .base import BaseProfileSupportingTask


class ListDefinedServices(BaseProfileSupportingTask):
    """Lists all defined containers in YAML files (can be limited by --profile selector)"""

    def get_group_name(self) -> str:
        return ':harbor:service'

    def get_name(self) -> str:
        return ':list'

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
