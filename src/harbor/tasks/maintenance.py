import os
from argparse import ArgumentParser
from abc import abstractmethod
from rkd.contract import ExecutionContext
from .base import HarborBaseTask
from ..formatting import prod_formatting


class BaseMaintenanceManagementTask(HarborBaseTask):
    def get_group_name(self) -> str:
        return ':harbor:maintenance'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--domain', '-d', help='Domain name', default='')
        parser.add_argument('--global', '-g', help='Set maintenance for all domains', action='store_true')

    def run(self, context: ExecutionContext) -> bool:
        path = self.get_data_path(context) + '/maintenance-mode'

        if context.get_arg('--global') and context.get_arg('--domain'):
            self.io().error_msg('Cannot use both --global and --domain switch')
            return False

        if context.get_arg('--global'):
            path += '/on'
        elif context.get_arg('--domain'):
            path += '/%s-on' % context.get_arg('--domain')
        else:
            self.io().error_msg('Must specify --global or --domain switch')
            return False

        try:
            return self.act(path)
        except PermissionError as e:
            self.io().error_msg('No permissions to write to "%s". Set permissions or use sudo?' % path)
            return False

    @abstractmethod
    def act(self, path: str) -> bool:
        pass

    def format_task_name(self, name) -> str:
        return prod_formatting(name)


class MaintenanceOnTask(BaseMaintenanceManagementTask):
    """Turn on the maintenance mode"""

    def get_name(self) -> str:
        return ':on'

    def act(self, path: str) -> bool:
        with open(path, 'w') as f:
            f.write('We are on strike ;)')

        os.chmod(path, 0o755)

        self.io().success_msg('Maintenance mode is on')

        return True


class MaintenanceOffTask(BaseMaintenanceManagementTask):
    """Turn on the maintenance mode"""

    def get_name(self) -> str:
        return ':off'

    def act(self, path: str) -> bool:
        if os.path.isfile(path):
            os.unlink(path)

        self.io().success_msg('Maintenance mode is off')

        return True


class MaintenanceListTask:
    pass
