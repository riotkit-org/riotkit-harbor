
import os
from argparse import ArgumentParser
from abc import abstractmethod
from tabulate import tabulate
from rkd.api.contract import ExecutionContext
from .base import HarborBaseTask
from ..formatting import development_formatting


class ListConfigsTask(HarborBaseTask):
    """Gets environment variable value"""

    def get_name(self) -> str:
        return ':list'

    def get_group_name(self) -> str:
        return ':harbor:config'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def run(self, context: ExecutionContext) -> bool:
        src_root = self.get_apps_path(context)
        rows = []

        for env_type in ['conf', 'conf.dev']:
            for root, subdirs, files in os.walk(src_root + '/' + env_type):
                for file in files:
                    # disabled
                    if file.endswith('.yml.disabled') or file.endswith('.yaml.disabled'):
                        rows.append([env_type + '/' + file[0:-9], 'No'])
                        continue

                    if not file.endswith('.yml') and not file.endswith('.yaml'):
                        continue

                    # enabled
                    rows.append([env_type + '/' + file, 'Yes'])

        self.io().out(tabulate(rows, headers=['Config file', 'Enabled']))
        self.io().print_line()

        return True


class AbstractManageConfigTask(HarborBaseTask):
    git_commands_suffix: str = ''  # used in tests
    git_mv_command = 'git mv'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--name', '-n', required=True, help='Configuration file name')

    def get_group_name(self) -> str:
        return ':harbor:config'

    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def run(self, context: ExecutionContext) -> bool:
        config_name = context.get_arg('--name').replace('..', '')
        src_path = self.get_apps_path(context) + '/' + config_name + self.get_from_suffix()
        dst_path = self.get_apps_path(context) + '/' + config_name + self.get_dest_suffix()

        if not os.path.isfile(src_path):
            self.io().error_msg('Cannot find file at path "%s", check if name is correct' % src_path)
            return False

        self.sh((self.git_mv_command + ' "%s" "%s"' + self.git_commands_suffix) % (src_path, dst_path))
        self.sh(('git add "%s"' + self.git_commands_suffix) % dst_path)
        self.rkd([':harbor:config:list'])

        return True

    @staticmethod
    @abstractmethod
    def get_from_suffix():
        pass

    @staticmethod
    @abstractmethod
    def get_dest_suffix():
        pass


class EnableConfigTask(AbstractManageConfigTask):
    """Enable a configuration file - YAML"""

    def get_name(self) -> str:
        return ':enable'

    @staticmethod
    def get_from_suffix():
        return '.disabled'

    @staticmethod
    def get_dest_suffix():
        return ''


class DisableConfigTask(AbstractManageConfigTask):
    """Disable a configuration file - YAML"""

    def get_name(self) -> str:
        return ':disable'

    @staticmethod
    def get_from_suffix():
        return ''

    @staticmethod
    def get_dest_suffix():
        return '.disabled'
