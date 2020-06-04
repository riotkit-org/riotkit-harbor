"""
Operations on containers

:author: Blackandred <riotkit .. riseup.net>
"""

import os
import re
from typing import Optional
from json import loads as json_loads
from .interface import HarborTaskInterface


class Container(object):
    """Running or stopped container model retrieved from docker inspection"""

    name: str
    inspection: dict

    def __init__(self, name: str, inspection: dict):
        self.name = name
        self.inspection = inspection

    def get_health_status(self) -> str:
        try:
            return self.inspection['State']['Health']['Status']
        except KeyError:
            return 'healthy' if self.inspection['State']['Status'] == 'running' else 'unhealthy'

    def has_health_check(self):
        try:
            self.inspection['State']['Health']['Status']
        except KeyError:
            return False

        return True

    def get_health_check_command(self) -> Optional[str]:
        try:
            return ' '.join(self.inspection['Config']['Healthcheck']['Test'][1:])
        except KeyError:
            return None


class ComposeContainerOperator(object):
    """Container operations - via docker-compose
    """

    scope: HarborTaskInterface
    project_name: str

    def __init__(self, scope: HarborTaskInterface, project_name: str):
        self.scope = scope
        self.project_name = project_name

    def build_operator_commandline_arguments(self, src_root: str, is_dev: bool) -> str:
        """Internal method: Builds list of docker-compose arguments
        """

        yamls = build_compose_files_list(src_root, is_dev)
        args = ' --project-directory=%s -p %s ' % (os.getcwd(), self.project_name)

        for yaml_path in yamls:
            args += ' -f %s ' % yaml_path

        return args

    def get_last_container_name(self, service_name: str) -> str:
        """Gets full container name of last deployed service
        """

        service_name = self.project_name + '_' + service_name + '_'
        ps = self.scope.sh('docker ps --format=\'{{ .Names }}\' | grep "%s"' % service_name, capture=True).split("\n")
        instance_numbers = []

        for instance in ps:
            matches = re.findall(service_name + '([0-9]+)', instance)

            if matches:
                instance_numbers.append(int(matches[0]))

        return service_name + str(max(instance_numbers))

    def get_container_name_for_service(self, service_name: str):
        return self.get_last_container_name(service_name)

    def inspect(self, container_name: str):
        """Inspects a running/stopped container"""

        out = self.scope.sh('docker inspect %s' % container_name, capture=True)
        as_json = json_loads(out)

        if not as_json:
            raise Exception('Cannot inspect container, unknown docker inspect output: %s' % out)

        return Container(container_name, as_json[0])


def build_compose_files_list(src_root: str, is_dev: bool) -> list:
    """Lists all YAML files to include in docker-compose arguments
    """

    yamls = {
        'conf': ['docker-compose.yml'],
        'conf.dev': []
    }

    for env_type in yamls.keys():
        for root, subdirs, files in os.walk(src_root + '/' + env_type):
            for file in files:
                if not file.endswith('.yml') and not file.endswith('.yaml'):
                    continue

                yamls[env_type].append(root + '/' + file)

    if is_dev:
        return yamls['conf'] + yamls['conf.dev']

    return yamls['conf']
