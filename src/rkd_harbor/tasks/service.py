import subprocess
import json
from time import time
from time import sleep
from contextlib import contextmanager
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from .base import HarborBaseTask
from .base import UpdateStrategy
from ..exception import ServiceNotCreatedException
from ..service import ServiceDeclaration


class BaseHarborServiceTask(HarborBaseTask):
    """Abstract class"""

    def get_group_name(self) -> str:
        return ':harbor:service'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)

        parser.add_argument('name', help='Service name')
        parser.add_argument('--extra-args', '-c', help='Optional compose arguments', default='')

    def prepare_tuple_for_single_container(self, ctx: ExecutionContext) -> tuple:
        service_name = ctx.get_arg('--name')
        service = self.services(ctx).get_by_name(service_name)
        instance_num = int(ctx.get_arg('--instance-num')) if ctx.get_arg('--instance-num') else None
        container_name = self.containers(ctx).find_container_name(service, instance_num)

        if not container_name:
            self.io().error_msg('Container not found')
            return None, None, None

        return container_name, service, instance_num

    def get_all_images_for_service(self, ctx: ExecutionContext, service: ServiceDeclaration):
        try:
            container_names = self.containers(ctx).find_all_container_names_for_service(service)
            inspected = self.containers(ctx).inspect_containers(container_names)

            return list(map(lambda container: container.get_image(), inspected))

        except ServiceNotCreatedException:
            # case: the service is just created, wasn't started yet
            return []


class ServiceUpTask(BaseHarborServiceTask):
    """Starts a single service

    Strategies:
        1) rolling: Perform a rolling update - scale services into more instances, and turn off older
                    containers silently (without downtime, requires extra resources)

           NOTICE: Do not use with databases

        2) compose: Perform a standard docker-compose up-like, if service is up-to-date then does not update, does not remove volumes

        3) recreate: Removes container and creates a new one, does not affect volumes

        3) auto (default): Performs automatic selection basing on label "org.riotkit.updateStrategy", defaults to "compose"
    """

    def get_name(self) -> str:
        return ':up'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--dont-recreate', '-d', action='store_true', help='Don\'t recreate the container if' +
                                                                               ' already existing (compose only)')
        parser.add_argument('--strategy', '-s',
                            help='Enforce an update strategy (optional)',
                            default='auto',
                            type=UpdateStrategy, choices=list(UpdateStrategy))
        parser.add_argument('--remove-previous-images', action='store_true',
                            help='Remove previous images if service had changed docker image')

    def run(self, context: ExecutionContext) -> bool:
        service_name = context.get_arg('name')
        strategy = str(context.get_arg('--strategy'))
        remove_previous_images = bool(context.get_arg('--remove-previous-images'))
        service = self.services(context).get_by_name(service_name)

        strategies = {
            'rolling': lambda: self.deploy_rolling(service, context),
            'compose': lambda: self.deploy_compose_like(service, context),
            'recreate': lambda: self.deploy_recreate(service, context)
        }

        with self.hooks_executed(context, 'service-start-%s' % service_name):
            with self._old_images_clean_up(context, service, clear_images=remove_previous_images):
                if strategy in strategies:
                    return strategies[strategy]()
                else:
                    if strategy == 'auto':
                        strategy = service.get_update_strategy(default='compose')

                        if strategy in strategies:
                            return strategies[strategy]()

                    self.io().error_msg('Invalid strategy selected: %s' % strategy)
                    return False

    @contextmanager
    def _old_images_clean_up(self, ctx: ExecutionContext, service: ServiceDeclaration, clear_images: bool):
        """Collects images, performs callback, then removes old images
        """

        if not clear_images:
            yield
            return

        self.io().debug('Finding all container names for service "%s"' % service.get_name())
        images = self.get_all_images_for_service(ctx, service)

        self.io().debug('OK, images collected')
        yield

        for image in images:
            # docker build was run locally
            if image is None:
                continue

            try:
                self.io().info('Trying to clean up image "%s"' % image)
                self.containers(ctx).rm_image(image, capture=True)
            except:
                self.io().warn('Cannot clean up image: "%s" [ignored, may be in use]' % image)

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
                    existing_containers = self.containers(ctx).scale_one_up(service)

                    self.rkd([
                        '--no-ui',
                        ':harbor:service:wait-for',
                        service.get_name(),
                        '--instance=%s' % max(existing_containers.keys())
                    ])

                    self.containers(ctx).kill_older_replica_than(
                        service,
                        self.get_project_name(ctx),
                        existing_containers,
                        processed + 1
                    )

                except Exception as e:
                    self.io().error('Scaling back to declared state as error happened: %s' % str(e))
                    self.containers(ctx).scale_to_desired_state(service)
                    raise e

                processed += 1

            self.io().print_opt_line()

        return True

    def deploy_compose_like(self, service: ServiceDeclaration, ctx: ExecutionContext) -> bool:
        """Regular docker-compose up deployment (with downtime)"""

        self.io().info('Performing "compose" deployment for "%s"' % service.get_name())
        self.containers(ctx).up(service,
                                norecreate=bool(ctx.get_arg('--dont-recreate')),
                                extra_args=ctx.get_arg('--extra-args'))

        return True

    def deploy_recreate(self, service: ServiceDeclaration, ctx: ExecutionContext) -> bool:
        """Regular docker-compose up deployment (with downtime)"""

        self.io().info('Performing "recreate" deployment for "%s"' % service.get_name())
        self.containers(ctx).up(service,
                                norecreate=False, force_recreate=True,
                                extra_args=ctx.get_arg('--extra-args'))

        return True


class ServiceRemoveTask(BaseHarborServiceTask):
    """Stops and removes a container and it's images

    Use --with-image to remove images of all service instances
    """

    def get_name(self) -> str:
        return ':rm'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--with-image', '-w', help='Remove also images', action='store_true')

    def run(self, ctx: ExecutionContext) -> bool:
        service_name = ctx.get_arg('name')
        service = self.services(ctx).get_by_name(service_name)
        with_image = ctx.get_arg('--with-image')
        images = self.get_all_images_for_service(ctx, service) if with_image else []

        self.containers(ctx).rm(service, extra_args=ctx.get_arg('--extra-args'))

        for image in images:
            try:
                self.containers(ctx).rm_image(image, capture=True)
            except:
                pass

        return True


class ServiceStopTask(BaseHarborServiceTask):
    """Brings down the service without deleting the container
    """

    def get_name(self) -> str:
        return ':stop'

    def run(self, ctx: ExecutionContext) -> bool:
        service_name = ctx.get_arg('name')
        self.containers(ctx).stop(service_name, extra_args=ctx.get_arg('--extra-args'))

        return True


class ExecTask(BaseHarborServiceTask):
    """Execute a command in a container"""

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--instance-num', '-i', default=None, help='Instance number. If None, then will pick last.')
        parser.add_argument('--command', '-e', default='/bin/sh', help='Command to execute')
        parser.add_argument('--shell', '-s', default='/bin/sh', help='Shell to use eg. bash or sh')
        parser.add_argument('--no-tty', help='Do not allocate tty', action='store_false')
        parser.add_argument('--no-interactive', help='Do not open interactive session', action='store_false')

    def get_name(self) -> str:
        return ':exec'

    def run(self, ctx: ExecutionContext) -> bool:
        command = ctx.get_arg('--command')
        shell = ctx.get_arg('--shell')
        tty = bool(ctx.get_arg('--no-tty'))
        interactive = bool(ctx.get_arg('--no-interactive'))

        container_name, service, instance_num = self.prepare_tuple_for_single_container(ctx)

        if not service:
            return False

        if shell != '/bin/sh' and command == '/bin/sh':
            command = shell

        self.containers(ctx).exec_in_container_passthrough(
            command, service, instance_num, shell=shell, tty=tty, interactive=interactive
        )

        return True


class GetContainerNameTask(BaseHarborServiceTask):
    """Returns a full container name - can be used in scripting"""

    def get_name(self) -> str:
        return ":get-container-name"

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--instance-num', '-i', default=None, help='Instance number. If None, then will pick last.')

    def run(self, ctx: ExecutionContext) -> bool:
        container_name, service, instance_num = self.prepare_tuple_for_single_container(ctx)
        self.io().out(container_name)

        return True


class InspectContainerTask(BaseHarborServiceTask):
    """Inspect a single container"""

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--instance-num', '-i', default=None, help='Instance number')

    def get_name(self) -> str:
        return ':inspect'

    def run(self, ctx: ExecutionContext) -> bool:
        container_name, service, instance_num = self.prepare_tuple_for_single_container(ctx)

        if not service:
            return False

        container = self.containers(ctx).inspect_container(container_name)

        self.io().outln(json.dumps(container.to_dict(), indent=4, sort_keys=True))
        return True


class AnalyzeServiceTask(BaseHarborServiceTask):
    """Report status of a service"""

    def get_name(self) -> str:
        return ':report'

    def run(self, ctx: ExecutionContext) -> bool:
        service_name = ctx.get_arg('name')
        service = self.services(ctx).get_by_name(service_name)

        if not service:
            self.io().error_msg('Service not found')
            return False

        try:
            containers = self.containers(ctx).find_all_container_names_for_service(service)
        except ServiceNotCreatedException:
            containers = []

        self.print_service_summary(ctx, service, len(containers))
        self.io().print_line()

        if containers:
            self.print_containers_summary(ctx, service, containers)

        return True

    def print_service_summary(self, ctx: ExecutionContext, service: ServiceDeclaration, replicas_active: int):
        summary_body = [
            ['Replicas:', '%i of %i' % (replicas_active, service.get_desired_replicas_count())],
            ['Update strategy:', service.get_update_strategy()],
            ['Declared image:', service.get_image()],
            ['Startup priority:', service.get_priority_number()]
        ]

        self.io().outln(self.table(
            [],
            summary_body
        ))

    def print_containers_summary(self, ctx: ExecutionContext, service: ServiceDeclaration, containers: list):
        inspected = self.containers(ctx).inspect_containers(containers)

        #
        # containers summary
        #
        summary_body = []

        for container in inspected:
            summary_body.append([
                container.get_name(),
                ('(!!) ' if service.get_image() != container.get_image() else '') + container.get_image(),
                container.get_health_status(),
                container.get_start_time()
            ])

        self.io().outln(self.table(
            ['Name', 'Actual image', 'Status', 'Started'],
            summary_body
        ))


class LogsTask(BaseHarborServiceTask):
    """Display logs"""

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--instance-num', '-i', default=None, help='Instance number')
        parser.add_argument('--follow', '-f', help='Follow the output', action='store_true')
        parser.add_argument('--buffered', help='Buffer output', action='store_true')

    def get_name(self) -> str:
        return ':logs'

    def run(self, ctx: ExecutionContext) -> bool:
        container_name, service, instance_num = self.prepare_tuple_for_single_container(ctx)
        buffered = bool(ctx.get_arg('--buffered'))

        if not service:
            self.io().error_msg('Service not found')
            return False

        self.io().outln(
            self.containers(ctx).get_logs(service, instance_num, raw=not buffered, follow=bool(ctx.get_arg('--follow')))
        )

        return True


class WaitForServiceTask(BaseHarborServiceTask):
    """Wait for service to be online"""

    def get_name(self) -> str:
        return ':wait-for'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--instance', '-i', required=False, help='Instance name, full container name')
        parser.add_argument('--timeout', '-t', default='120', help='Timeout in seconds')

    def run(self, ctx: ExecutionContext) -> bool:
        service_name = ctx.get_arg('name')
        timeout = int(ctx.get_arg('--timeout'))
        instance_num = int(ctx.get_arg('--instance')) if ctx.get_arg('--instance') else None

        service = self.services(ctx).get_by_name(service_name)

        try:
            container_name = self.containers(ctx).find_container_name(service, instance_num)
            container = self.containers(ctx).inspect_container(container_name)
        except ServiceNotCreatedException as e:
            self.io().error_msg(str(e))
            return False

        started_at = time()

        self.io().info('Checking health of "%s" service - %s' % (service_name, container_name))

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
                        command = container.get_health_check_command().replace('"', '\\"')

                        self.containers(ctx).exec_in_container(
                            service_name=service_name,
                            command='/bin/sh -c "%s"' % command,
                            instance_num=instance_num
                        )

                        self.io().success_msg('Service healthy after %is' % (time() - started_at))
                        return True

                    except subprocess.CalledProcessError as e:
                        self.io().debug(str(e.output)[0:128])
                        sleep(1)
                        continue

                if health == 'healthy' or health == 'running':
                    self.io().success_msg('Service healthy after %i' % (time() - started_at))
                    return True

                sleep(1)
        else:
            self.io().warn('Instance has no healthcheck defined!')

        return True
