
import os
from tabulate import tabulate
from rkd.contract import ExecutionContext
from .base import HarborBaseTask


class ListConfigsTask(HarborBaseTask):
    """Gets environment variable value"""

    def get_name(self) -> str:
        return ':list'

    def get_group_name(self) -> str:
        return ':harbor:config'

    def run(self, context: ExecutionContext) -> bool:
        src_root = self.get_apps_path(context)
        rows = []

        for env_type in ['conf', 'conf.dev']:
            for root, subdirs, files in os.walk(src_root + '/' + env_type):
                for file in files:
                    # disabled
                    if file.endswith('.yml.disabled') or file.endswith('.yaml.disabled'):
                        rows.append([env_type + '/' + file, 'No'])
                        continue

                    if not file.endswith('.yml') and not file.endswith('.yaml'):
                        continue

                    # enabled
                    rows.append([env_type + '/' + file, 'Yes'])

        self.io().out(tabulate(rows, headers=['Config file', 'Enabled']))

        return True
