import subprocess
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
        parser.add_argument('--extra-args', '-c', help='Optional compose arguments', default='')


class ServiceUpTask(BaseHarborServiceTask):
    """Starts a single service

    Strategies:
        1) rolling: Perform a rolling update - scale services into more instances, and turn off older
                    containers silently (without downtime, requires extra resources)

           NOTICE: Do not use with databases

        2) enforced: Perform an enforced update with a downtime (regular docker-compose behavior)

        3) auto (default): Performs automatic selection basing on label "org.riotkit.updateStrategy", defaults to "compose"
    """

    def get_name(self) -> str:
        return ':up'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--dont-recreate', '-d', action='store_true', help='Don\'t recreate the container if' +
                                                                               ' already existing (compose only)')
        parser.add_argument('--strategy', '-s', default='auto', help='Deployment strategy: rolling, compose, auto')

    def run(self, context: ExecutionContext) -> bool:
        service_name = context.get_arg('--name')
        strategy = context.get_arg('--strategy')
        service = self.services(context).get_by_name(service_name)

        strategies = {
            'rolling': lambda: self.deploy_rolling(service, context),
            'compose': lambda: self.deploy_enforced(service, context)
        }

        if strategy in strategies:
            return strategies[strategy]()
        else:
            if strategy == 'auto':
                strategy = service.get_update_strategy(default='compose')

                if strategy in strategies:
                    return strategies[strategy]()

            self.io().error_msg('Invalid strategy selected')
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

            with self.containers(ctx).service_discovery_stopped():
                try:
                    new_replica_name = self.containers(ctx).scale_one_up(service)
                    self.rkd([
                        ':harbor:service:wait-for',
                        '--name=%s' % service.get_name(),
                        '--instance=%s' % new_replica_name]
                    )

                    self.containers(ctx).kill_older_replica_than(new_replica_name, processed)

                except Exception as e:
                    self.io().error('Scaling back to declared state as error happened: %s' % str(e))
                    self.containers(ctx).scale_to_desired_state(service)
                    raise e

                processed += 1

        return True

    def deploy_enforced(self, service: ServiceDeclaration, ctx: ExecutionContext) -> bool:
        """Regular docker-compose up deployment (with downtime)"""

        self.io().info('Performing "enforced" deployment for "%s"' % service.get_name())
        self.containers(ctx).up(service,
                                norecreate=bool(ctx.get_arg('--dont-recreate')),
                                extra_args=ctx.get_arg('--extra-args'))

        return True


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
        service = self.services(ctx).get_by_name(service_name)
        is_removing_image = ctx.get_arg('--with-image')
        img_to_remove = ''

        if is_removing_image:
            inspected = self.containers(ctx).inspect(service_name)

            if inspected:
                img_to_remove = inspected['Image']

        self.containers(ctx).rm(service, extra_args=ctx.get_arg('--extra-args'))

        if img_to_remove:
            try:
                self.containers(ctx).rm_image(img_to_remove)
            except:
                pass

        return True


class ServiceDownTask(BaseHarborServiceTask):
    """Brings down the service without deleting the container
    """

    def get_name(self) -> str:
        return ':down'

    def run(self, ctx: ExecutionContext) -> bool:
        service_name = ctx.get_arg('--name')
        self.containers(ctx).stop(service_name, extra_args=ctx.get_arg('--extra-args'))

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
        container = self.containers(ctx).inspect(self.containers(ctx).get_last_container_name_for_service(service_name))
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
                        self.containers(ctx).exec_in_container(
                            service_name=service_name,
                            command='/bin/sh -c "%s" >/dev/null 2>&1',
                            instance_num=instance_num
                        )

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
