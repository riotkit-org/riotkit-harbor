import re
import subprocess
from contextlib import contextmanager
from argparse import ArgumentParser
from rkd.contract import ExecutionContext
from .base import HarborBaseTask
from ..service import ServiceDeclaration
from time import time
from time import sleep


class BaseHarborServiceTask(HarborBaseTask):
    """Abstract class"""

    def get_group_name(self) -> str:
        return ':harbor:service'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)

        parser.add_argument('--name', '-n', required=True, help='Service name')
        parser.add_argument('--compose-args', '-c', help='Optional compose arguments', default='')


class ServiceUpTask(BaseHarborServiceTask):
    """Starts a single service

    Strategies:
        1) rolling: Perform a rolling update - scale services into more instances, and turn off older
                    containers silently (without downtime, requires extra resources)

           NOTICE: Do not use with databases

        2) enforced: Perform an enforced update with a downtime (regular docker-compose behavior)
    """

    def get_name(self) -> str:
        return ':up'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--dont-recreate', '-d', action='store_true', help='Don\'t recreate the container if' +
                                                                               ' already existing (enforced only)')
        parser.add_argument('--strategy', '-s', default='rolling', help='Deployment strategy: rolling, enforced')

    def run(self, context: ExecutionContext) -> bool:
        service_name = context.get_arg('--name')
        strategy = context.get_arg('--strategy')
        service = self.services().get_by_name(service_name)

        if strategy == 'rolling':
            return self.deploy_rolling(service, context)
        elif strategy == 'enforced':
            return self.deploy_enforced(service, context)
        else:
            self.io().error_msg('Invalid value for --strategy switch')
            return False

    def deploy_rolling(self, service: ServiceDeclaration, ctx: ExecutionContext) -> bool:
        """Rolling-update (without a downtime)

        1. Stop service discovery (to not add our not-ready-yet container to the load balancing)
        2. Scale up service one by one
        3. When health check is OK, then turn off older instance
        4. Start service discovery
        5. Repeat until get replaced all of the replicas
        """

        self.io().info('Doing a "rolling" deployment for "%s"' % service.get_name())
        desired_replicas = service.get_desired_replicas_count()
        processed = 0

        for replica_num in range(1, desired_replicas + 1):
            self.io().info('Processing instance #%i/%i' % (replica_num, desired_replicas))

            with self._service_discovery_stopped():
                try:
                    new_replica_name = self._scale_one_up(service)
                    self.rkd([
                        ':harbor:service:wait-for',
                        '--name=%s' % service.get_name(),
                        '--instance=%s' % new_replica_name]
                    )

                    self._kill_older_replica_than(new_replica_name, processed)

                except Exception as e:
                    self.io().error('Scaling back to declared state as error happened: %s' % str(e))
                    self._scale_to_desired_state(service)
                    raise e

                processed += 1

        return True

    def deploy_enforced(self, service: ServiceDeclaration, ctx: ExecutionContext) -> bool:
        """Regular docker-compose up deployment (with downtime)"""

        recreate = '--no-recreate' if ctx.get_arg('--dont-recreate') else ''

        self.io().info('Performing "enforced" deployment for "%s"' % service.get_name())

        self.compose([
            'up', '-d', recreate,
            '--scale %s=%i' % (service.get_name(), service.get_desired_replicas_count()),
            service.get_name(),
            ctx.get_arg('--compose-args')
        ])
        return True

    def _kill_older_replica_than(self, replica_name: str, already_killed: int = 0):
        """Kill first old replica on the list"""

        current_num = int(replica_name.split('_')[-1])
        previous_num = current_num - already_killed - 1
        service_full_name = '_'.join(replica_name.split('_')[:-1])

        self.io().info('Replica "%s" was spawned, killing older instance' % replica_name)
        self.io().info('Killing replica num=%i' % previous_num)
        self.sh('docker rm -f "%s_%i"' % (service_full_name, previous_num))

    def _scale_one_up(self, service: ServiceDeclaration) -> str:
        """Scale up and return last instance name (docker container name)"""

        desired_replicas = service.get_desired_replicas_count()
        self.io().info('Scaling up to %i' % (desired_replicas + 1))

        out = self.compose(['up', '-d', '--scale %s=%i' %
                            (service.get_name(), desired_replicas + 1), service.get_name(), '2>&1'],
                           capture=True)

        self.io().info('Finding last instance name...')
        results = re.findall('([A-Za-z\-_]+)_([0-9]+)', out)
        container_numbers = list(map(lambda matches: int(matches[1]), results))

        last_instance_name = results[0][0] + '_' + str(max(container_numbers))
        self.io().info('OK, it is "%s"' % last_instance_name)

        return last_instance_name

    def _scale_to_desired_state(self, service: ServiceDeclaration):
        """Scale to declared state - eg. in case of a failure"""

        self.compose(
            ['up', '-d',
             '--scale %s=%i' % (service.get_name(), service.get_desired_replicas_count()), service.get_name(), '2>&1']
        )

    @contextmanager
    def _service_discovery_stopped(self):
        """Stops a service discovery for a moment"""

        try:
            self.io().info('Suspending service discovery')
            self.compose(['stop', 'gateway_proxy_gen'])
            yield
        finally:
            self.io().info('Starting service discovery')
            self.compose(['start', 'gateway_proxy_gen'])


class ServiceRemoveTask(BaseHarborServiceTask):
    """Stops and removes a container and it's images
    """

    def get_name(self) -> str:
        return ':rm'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--with-image', '-i',
                            help='Decide if want to also untag/delete image locally', action='store_true')

    def run(self, ctx: ExecutionContext) -> bool:
        service_name = ctx.get_arg('--name')
        is_removing_image = ctx.get_arg('--with-image')
        img_to_remove = ''

        if is_removing_image:
            inspected = self.containers(ctx).inspect(service_name)

            if inspected:
                img_to_remove = inspected['Image']

        self.compose(['rm', '--stop', '--force', service_name, ctx.get_arg('--compose-args')])

        if img_to_remove:
            try:
                self.sh('docker rmi %s' % img_to_remove)
            except:
                pass

        return True


class ServiceDownTask(BaseHarborServiceTask):
    """Brings down the service without deleting the container
    """

    def get_name(self) -> str:
        return ':down'

    def run(self, context: ExecutionContext) -> bool:
        service_name = context.get_arg('--name')

        self.compose(['stop', service_name, context.get_arg('--compose-args')])
        return True


class WaitForServiceTask(BaseHarborServiceTask):
    """Wait for service to be online"""

    def get_name(self) -> str:
        return ':wait-for'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--instance', '-i', required=True, help='Instance name, full container name')
        parser.add_argument('--timeout', '-t', default='120', help='Timeout in seconds')

    def run(self, ctx: ExecutionContext) -> bool:
        service_name = ctx.get_arg('--name')
        timeout = int(ctx.get_arg('--timeout'))

        instance_num = int(ctx.get_arg('--instance').split('_')[-1])
        container = self.containers(ctx).inspect(self.containers(ctx).get_container_name_for_service(service_name))
        started_at = time()

        self.io().info('Checking health of "%s" service - instance #%i' % (service_name, instance_num))

        if container.has_health_check():
            while True:
                if time() - started_at >= timeout:
                    self.io().error_msg('Timeout of %is reached.' % timeout)
                    return False

                health = container.get_health_status()

                # do not wait for result, do check manually in mean time
                if health == 'starting':
                    self.io().warn('Docker reports "starting" - performing a manual check, we wont wait for docker')

                    try:
                        self.compose([
                            'exec', '-T',
                            '--index=%i' % instance_num,
                            service_name,
                            '/bin/sh', '-c', '"%s"' % container.get_health_check_command(),
                            '>/dev/null', '2>&1'
                        ], capture=True)

                        self.io().success_msg('Service healthy after %is' % (time() - started_at))
                        return True

                    except subprocess.CalledProcessError:
                        sleep(1)
                        continue

                if health == 'healthy' or health == 'running':
                    self.io().success_msg('Service healthy after %i' % (time() - started_at))
                    return True

                sleep(1)
        else:
            self.io().warn('Instance has no healthcheck defined!')

        return True
