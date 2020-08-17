from argparse import ArgumentParser
from subprocess import CalledProcessError
from rkd.api.contract import ExecutionContext
from .base import BaseProfileSupportingTask
from .base import UpdateStrategy


class StartTask(BaseProfileSupportingTask):
    """Create and start containers
    """
    
    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--strategy', '-s',
                            help='Enforce an update strategy (optional)',
                            default='auto',
                            type=UpdateStrategy, choices=list(UpdateStrategy))
        parser.add_argument('--remove-previous-images', action='store_true',
                            help='Remove previous images if service had changed docker image')

    def get_name(self) -> str:
        return ':start'

    def run(self, context: ExecutionContext) -> bool:
        services = self.get_matching_services(context)
        strategy = context.get_arg('--strategy')
        result = True

        with self.hooks_executed(context, 'start'):
            for service in services:
                self.io().h2('Starting "%s" (%i instances)...' % (service.get_name(), service.get_desired_replicas_count()))

                try:
                    self.rkd(
                        [
                            '--no-ui',
                            ':harbor:service:up',
                            service.get_name(),
                            '--remove-previous-images' if context.get_arg('--remove-previous-images') else '',
                            ('--strategy=%s' % strategy) if strategy else ''
                        ],
                        capture=not self.io().is_log_level_at_least('info')
                    )

                    self.io().success_msg('Service "%s" was started' % service.get_name())

                except CalledProcessError as e:
                    self.io().err(str(e))
                    self.io().error_msg('Cannot start service "%s"' % service.get_name())
                    result = False

                self.io().print_opt_line()

        return result


class StopTask(BaseProfileSupportingTask):
    """Stop running containers (preserving the order - the gateway should be turned off first)
    """

    def get_name(self) -> str:
        return ':stop'

    def run(self, ctx: ExecutionContext) -> bool:
        services = self.get_matching_services(ctx)

        for service in services:
            self.io().info('Stopping "%s"' % service.get_name())
            self.containers(ctx).stop(service.get_name())

        return True


class RestartTask(BaseProfileSupportingTask):
    """Restart running containers
    """

    def get_name(self) -> str:
        return ':restart'

    def run(self, ctx: ExecutionContext) -> bool:
        services = self.get_matching_services(ctx)

        for service in services:
            self.io().info('Restarting "%s"' % service.get_name())
            self.containers(ctx).restart(service.get_name())

        return True


class StopAndRemoveTask(BaseProfileSupportingTask):
    """Forcibly stop running containers and remove (keeps volumes)

    Use --with-image to delete image of each service
    """

    def get_name(self) -> str:
        return ':remove'

    def configure_argparse(self, parser: ArgumentParser):
        super(StopAndRemoveTask, self).configure_argparse(parser)
        parser.add_argument('--with-image', help='Remove containers with images', action='store_true')

    def run(self, ctx: ExecutionContext) -> bool:
        services = self.get_matching_services(ctx)

        for service in services:
            self.io().info('Removing "%s"' % service.get_name())
            self.rkd([
                ':harbor:service:rm',
                service.get_name(),
                '--with-image' if ctx.get_arg('--with-image') else ''
            ])

        return True


class PullTask(BaseProfileSupportingTask):
    """Pull images specified in containers definitions
    """

    def get_name(self) -> str:
        return ':pull'

    def run(self, ctx: ExecutionContext) -> bool:
        self.containers(ctx).pull(self.get_matching_service_names(ctx))

        return True


class UpgradeTask(BaseProfileSupportingTask):
    """Begin an upgrade procedure

    Behavior:
     1. Render templates using :harbor:templates:render
     2. Pull all images
     3. Pull all git repositories
     4. Upgrade services one-by-one
     5. Restart gateway
     6. Call SSL to refresh
    """

    def get_name(self) -> str:
        return ':upgrade'

    def configure_argparse(self, parser: ArgumentParser):
        super(UpgradeTask, self).configure_argparse(parser)
        parser.add_argument('--strategy', '-s',
                            help='Enforce an update strategy (optional)',
                            default='auto',
                            type=UpdateStrategy, choices=list(UpdateStrategy))
        parser.add_argument('--remove-previous-images', action='store_true',
                            help='Remove previous images if service had changed docker image')

    def run(self, context: ExecutionContext) -> bool:
        profile = context.get_arg('--profile')
        strategy = context.get_arg('--strategy')
        success = True

        with self.hooks_executed(context, 'upgrade'):
            self.rkd([
                '--no-ui',
                ':harbor:templates:render',
                ':harbor:pull', '--profile=%s' % profile,

                ':harbor:start', '--profile=%s' % profile, '--strategy=%s' % strategy,
                '--remove-previous-images' if context.get_arg('--remove-previous-images') else '',

                ':harbor:gateway:reload'
            ])

        return success
