"""
Operations on containers

Interacts directly with Docker and Docker-Compose. In the future it will be possible to integrate also Docker Swarm.

:author: Blackandred <riotkit .. riseup.net>
"""

import os
import re
import subprocess
from time import time
from contextlib import contextmanager
from typing import Optional
from typing import Dict
from collections import OrderedDict
from json import loads as json_loads
from rkd.contract import ExecutionContext
from .interface import HarborTaskInterface
from .service import ServiceDeclaration
from .exception import ServiceNotReadyException
from .exception import ServiceNotCreatedException


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

    def get_image(self) -> Optional[str]:
        try:
            return self.inspection['Config']['Image']
        except KeyError:
            return None


class ComposeDriver(object):
    """Performs container operations using docker-compose
    """

    scope: HarborTaskInterface
    ctx: ExecutionContext
    project_name: str

    # lazy
    _compose_args: str = None

    def __init__(self, scope: HarborTaskInterface, ctx: ExecutionContext, project_name: str):
        self.scope = scope
        self.project_name = project_name
        self.ctx = ctx

    def get_last_container_name_for_service(self, service_name: str) -> str:
        """Gets full container name of last deployed service (last instance name)
        """

        service_name = self.project_name + '_' + service_name + '_'
        ps = self.scope.sh('docker ps --format=\'{{ .Names }}\' | grep "%s"' % service_name, capture=True).split("\n")
        instance_numbers = []

        for instance in ps:
            matches = re.findall(service_name + '([0-9]+)', instance)

            if matches:
                instance_numbers.append(int(matches[0]))

        if not instance_numbers:
            raise ServiceNotCreatedException(service_name)

        return service_name + str(max(instance_numbers))

    def inspect_container(self, container_name: str):
        """Inspects a running/stopped container"""

        out = self.scope.sh('docker inspect %s' % container_name, capture=True)
        as_json = json_loads(out)

        if not as_json:
            raise Exception('Cannot inspect container, unknown docker inspect output: %s' % out)

        return Container(container_name, as_json[0])

    def inspect_containers(self, names: list):
        """Inspect multiple containers by name at once (does same as inspect_container()
        but has better performance for multiple containers at once)
        """

        out = self.scope.sh('docker inspect %s' % ' '.join(names), capture=True)
        as_json = json_loads(out)

        if not as_json:
            raise Exception('Cannot inspect container, unknown docker inspect output: %s' % out)

        containers = []
        num = 0

        for sub_json in as_json:
            containers.append(Container(names[num], sub_json))
            num += 1

        return containers

    @contextmanager
    def service_discovery_stopped(self):
        """Stops a service discovery for a moment"""

        try:
            self.scope.io().info('Suspending service discovery')
            self.compose(['stop', 'gateway_proxy_gen'])
            yield
        finally:
            self.scope.io().info('Starting service discovery')
            self.compose(['up', '-d', '--no-recreate', 'gateway_proxy_gen'])

    #
    # Methods to spawn processes in shell
    #
    def compose(self, arguments: list, capture: bool = False) -> Optional[str]:
        """Makes a call to docker-compose with all prepared arguments that should be"""

        cmd = 'docker-compose %s %s' % (self.get_compose_args(), ' '.join(arguments))
        self.scope.io().debug('Calling compose: %s' % cmd)

        return self.scope.sh(cmd, capture=capture)

    def exec_in_container(self, service_name: str, command: str, instance_num: int = None, capture: bool = True) -> str:
        """Executes a command in given container"""

        if instance_num is None:
            instance_num = int(self.get_last_container_name_for_service(service_name).split('_')[-1])

        return self.compose([
            'exec', '-T',
            '--index=%i' % instance_num if instance_num else '',
            service_name,
            'sh', '-c', '"', command, '"'
        ], capture=capture)

    def exec_in_container_passthrough(self, command: str, service: ServiceDeclaration, instance_num: int = None,
                                      shell: str = '/bin/sh'):
        container_name = self.find_container_name(service, instance_num)

        return subprocess.call(['docker', 'exec', '-it', container_name, shell, '-c', command])

    #
    # Basics - compose arguments present in all commands
    #
    def get_compose_args(self):
        """Gets arguments to use with docker-compose"""

        if not self._compose_args:
            # @todo: IS DEV implementation
            self._compose_args = self.create_compose_arguments(self.ctx.get_env('APPS_PATH'), is_dev=True)

            self.scope.io().debug('Compose args: %s' % self._compose_args)

        return self._compose_args

    def create_compose_arguments(self, src_root: str, is_dev: bool) -> str:
        """Internal method: Builds list of docker-compose arguments
        """

        yamls = build_compose_files_list(src_root, is_dev)
        args = ' --project-directory=%s -p %s ' % (os.getcwd(), self.project_name)

        for yaml_path in yamls:
            args += ' -f %s ' % yaml_path

        return args

    #
    # Domain specific methods
    #
    def up(self, service: ServiceDeclaration, norecreate: bool = False, force_recreate: bool = False,
           extra_args: str = ''):
        """Bring up the service"""

        self.compose([
            'up', '-d',
            '--no-recreate' if norecreate else '',
            '--force-recreate' if force_recreate else '',
            '--scale %s=%i' % (service.get_name(), service.get_desired_replicas_count()),
            service.get_name(),
            extra_args
        ])

    def find_container_name(self, service: ServiceDeclaration, instance_num: int = None) -> str:
        if not instance_num:
            return self.get_last_container_name_for_service(service.get_name())

        containers = self.get_created_containers(only_running=False)

        if not service.get_name() in containers:
            raise ServiceNotCreatedException('Invalid service name or no any containers were created')

        return self.create_container_name(service, instance_num)

    def create_container_name(self, service: ServiceDeclaration, instance_num: int) -> str:
        return self.project_name + '_' + service.get_name() + '_' + str(instance_num)

    def get_logs(self, service: ServiceDeclaration, instance_num: int = None, raw: bool = False) -> str:
        """Gets logs from given container

        Args:
            service: Service declaration
            instance_num: Replica number
            raw: Do not return result, pass it directly to stdout and to stderr

        Returns:
            Logs in text format
        """

        command = 'docker logs "%s" 2>&1' % self.find_container_name(service, instance_num)

        if raw:
            subprocess.call(command, shell=True)
            return ''

        return self.scope.sh(command, capture=True)

    def wait_for_log_message(self, text: str, service: ServiceDeclaration, instance_num: int = None,
                             timeout: int = 300):

        """Waits for a text to appear in docker log

        Args:
            text: Text to wait for
            service: Service declaration
            instance_num: Replica number
            timeout: Timeout in seconds

        Raises:
            ServiceNotReadyException
        """

        timeout_at = time() + timeout

        while time() < timeout_at:
            logs = self.get_logs(service, instance_num)

            if text in logs:
                return

        raise ServiceNotReadyException(service.get_name(), text, instance_num)

    def rm(self, service: ServiceDeclaration, extra_args: str = ''):
        self.compose(['rm', '--stop', '--force', service.get_name(), extra_args])

    def kill_older_replica_than(self, service: ServiceDeclaration, project_name: str,
                                existing_containers: Dict[int, bool],
                                already_killed: int = 0):
        """Kill first old replica on the list"""

        instance_index = (already_killed * -1) - 1
        previous_instance_num = list(existing_containers.items())[instance_index][0]
        service_full_name = project_name + '_' + service.get_name() + '_' + str(previous_instance_num)

        self.scope.io().info('Instances: ' + str(list(existing_containers.items())))
        self.scope.io().info('Previous instance selector: %i' % instance_index)

        self.scope.io().info('Replica "%s" was spawned, killing older instance' % service_full_name)
        self.scope.io().info('Killing replica num=%i' % previous_instance_num)
        self.scope.sh('docker rm -f "%s"' % service_full_name)

    def scale_one_up(self, service: ServiceDeclaration) -> Dict[int, bool]:
        """Scale up and return last instance name (docker container name)"""

        desired_replicas = service.get_desired_replicas_count()
        self.scope.io().info('Scaling up to %i' % (desired_replicas + 1))

        self.compose(
            ['up', '-d', '--no-deps',
             '--scale %s=%i' % (service.get_name(), desired_replicas + 1), service.get_name(), '2>&1'],
            capture=True
        )

        self.scope.io().info('Finding last instance name...')
        instances: Dict[int, bool] = self.get_created_containers(only_running=False)[service.get_name()]

        self.scope.io().info('OK, it is "%s"' % max(instances.keys()))

        return instances

    def scale_to_desired_state(self, service: ServiceDeclaration):
        """Scale to declared state - eg. in case of a failure"""

        self.compose(
            ['up', '-d', '--no-deps',
             '--scale %s=%i' % (service.get_name(), service.get_desired_replicas_count()),
             service.get_name(),
             '2>&1']
        )

    def rm_image(self, img_to_remove: str, capture: bool = False):
        self.scope.sh('docker rmi %s 2>&1' % img_to_remove, capture=capture)

    def stop(self, service_name: str, extra_args: str = ''):
        self.compose(['stop', service_name, extra_args])

    def ps(self, params: list):
        self.compose(['ps'] + params)

    def pull(self, services_names: list):
        self.compose(['pull'] + services_names)

    def get_created_containers(self, only_running: bool) -> Dict[str, Dict[int, bool]]:
        """Gets all running services"""

        instances = self.compose(['ps'], capture=True).strip().split("\n")
        counted = {}

        for instance in instances:
            matches = re.findall('([A-Za-z0-9\-_]+)_([0-9]+)\s*(.*)(Up|Exit)', instance)

            if not matches:
                continue

            matches = matches[0]
            service_name = matches[0][len(self.project_name + '_'):]
            is_up = matches[3].upper() == 'UP'

            if service_name not in counted:
                counted[service_name] = OrderedDict()

            if only_running and not is_up:
                continue

            counted[service_name][int(matches[1])] = is_up

        counted_and_sorted = {}

        for service in counted:
            counted_and_sorted[service] = OrderedDict(sorted(counted[service].items()))

        return counted

    def find_all_container_names_for_service(self, service: ServiceDeclaration) -> list:
        """Finds all created container names for given service name

        Args:
            service: Service declaration object
        """

        created = self.get_created_containers(only_running=False)

        if not service.get_name() in created:
            raise ServiceNotCreatedException(service.get_name())

        return list(
            map(
                lambda instance_num: self.create_container_name(service, instance_num),
                created[service.get_name()].keys()
            )
        )


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
