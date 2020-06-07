from argparse import ArgumentParser
from subprocess import CalledProcessError
from rkd.contract import ExecutionContext
from .base import HarborBaseTask
from .base import BaseProfileSupportingTask
from .base import UpdateStrategy


class ListContainersTask(HarborBaseTask):
    """List all containers
    """

    def get_group_name(self) -> str:
        return ':harbor:compose'

    def get_name(self) -> str:
        return ':ps'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--quiet', '-q', help='Only display IDs', action='store_true')
        parser.add_argument('--all', '-a', help='Show all containers, including stopped', action='store_true')

    def run(self, ctx: ExecutionContext) -> bool:
        params = []

        if ctx.get_arg('--quiet'):
            params.append('--quiet')

        if ctx.get_arg('--all'):
            params.append('--all')

        self.containers(ctx).ps(params)
        return True


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

        for service in services:
            self.io().h2('Starting "%s" (%i instances)...' % (service.get_name(), service.get_desired_replicas_count()))

            try:
                self.rkd(
                    [
                        '--no-ui',
                        ':harbor:service:up',
                        '--name=%s' % service.get_name(),
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
    """Stop running containers
    """

    def get_name(self) -> str:
        return ':stop'

    def run(self, context: ExecutionContext) -> bool:
        # @todo: Rewrite to use service.py
        return False


class RestartTask(BaseProfileSupportingTask):
    """Restart running containers
    """

    def get_name(self) -> str:
        return ':restart'

    def run(self, context: ExecutionContext) -> bool:
        # @todo: Rewrite to use service.py
        return False


class StopAndRemoveTask(BaseProfileSupportingTask):
    """Forcibly stop running containers and remove (keeps volumes)
    """

    def get_name(self) -> str:
        return ':remove'

    def run(self, context: ExecutionContext) -> bool:
        # @todo: Rewrite to use service.py
        return False


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
     1. Pull all images
     2. Pull all git repositories
     3. Upgrade services one-by-one
     4. Restart gateway
     5. Call SSL to refresh
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

        self.rkd([
            '--no-ui',
            ':harbor:pull', '--profile=%s' % profile,

            ':harbor:start', '--profile=%s' % profile, '--strategy=%s' % strategy,
            '--remove-previous-images' if context.get_arg('--remove-previous-images') else '',

            ':harbor:prod:gateway:reload'
        ])

        return success
