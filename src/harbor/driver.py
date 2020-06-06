"""
Operations on containers

Interacts directly with Docker and Docker-Compose. In the future it will be possible to integrate also Docker Swarm.

:author: Blackandred <riotkit .. riseup.net>
"""

import os
import re
from contextlib import contextmanager
from typing import Optional
from json import loads as json_loads
from rkd.contract import ExecutionContext
from .interface import HarborTaskInterface
from .service import ServiceDeclaration


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

        return service_name + str(max(instance_numbers))

    def inspect(self, container_name: str):
        """Inspects a running/stopped container"""

        out = self.scope.sh('docker inspect %s' % container_name, capture=True)
        as_json = json_loads(out)

        if not as_json:
            raise Exception('Cannot inspect container, unknown docker inspect output: %s' % out)

        return Container(container_name, as_json[0])

    @contextmanager
    def service_discovery_stopped(self):
        """Stops a service discovery for a moment"""

        try:
            self.scope.io().info('Suspending service discovery')
            self.compose(['stop', 'gateway_proxy_gen'])
            yield
        finally:
            self.scope.io().info('Starting service discovery')
            self.compose(['start', 'gateway_proxy_gen'])

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
        return self.compose([
            'exec', '-T',
            '--index=%i' % instance_num if instance_num else '',
            service_name,
            'sh', '-c', '"', command, '"'
        ], capture=capture)

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

    def rm(self, service: ServiceDeclaration, extra_args: str = ''):
        self.compose(['rm', '--stop', '--force', service.get_name(), extra_args])

    def kill_older_replica_than(self, replica_name: str, already_killed: int = 0):
        """Kill first old replica on the list"""

        current_num = int(replica_name.split('_')[-1])
        previous_num = current_num - already_killed - 1
        service_full_name = '_'.join(replica_name.split('_')[:-1])

        self.scope.io().info('Replica "%s" was spawned, killing older instance' % replica_name)
        self.scope.io().info('Killing replica num=%i' % previous_num)
        self.scope.sh('docker rm -f "%s_%i"' % (service_full_name, previous_num))

    def scale_one_up(self, service: ServiceDeclaration) -> str:
        """Scale up and return last instance name (docker container name)"""

        desired_replicas = service.get_desired_replicas_count()
        self.scope.io().info('Scaling up to %i' % (desired_replicas + 1))

        out = self.compose(['up', '-d', '--no-deps', '--scale %s=%i' %
                            (service.get_name(), desired_replicas + 1), service.get_name(), '2>&1'],
                           capture=True)

        self.scope.io().info('Finding last instance name...')
        results = re.findall('([A-Za-z\-_]+)_([0-9]+)', out)

        # compose can throw warnings eg. "orphan service XY", we need to filter out that
        results = list(filter(lambda match: match[0].endswith(service.get_name()), results))

        # reduce to numbers (last part)
        container_numbers = list(map(lambda matches: int(matches[1]), results))

        last_instance_name = results[0][0] + '_' + str(max(container_numbers))
        self.scope.io().info('OK, it is "%s"' % last_instance_name)

        return last_instance_name

    def scale_to_desired_state(self, service: ServiceDeclaration):
        """Scale to declared state - eg. in case of a failure"""

        self.compose(
            ['up', '-d', '--no-deps',
             '--scale %s=%i' % (service.get_name(), service.get_desired_replicas_count()),
             service.get_name(),
             '2>&1']
        )

    def rm_image(self, img_to_remove: str):
        self.scope.sh('docker rmi %s' % img_to_remove)

    def stop(self, service_name: str, extra_args: str = ''):
        self.compose(['stop', service_name, extra_args])

    def ps(self, params: list):
        self.compose(['ps'] + params)

    def pull(self, services_names: list):
        self.compose(['pull'] + services_names)

    def get_running_containers(self):
        """Gets all running services"""
        return self.compose(['ps', '--services'], capture=True).strip().split("\n")


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
