from argparse import ArgumentParser
from rkd.contract import ExecutionContext
from .base import HarborBaseTask
from .base import BaseProfileSupportingTask
from subprocess import CalledProcessError


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
        parser.add_argument('--no-recreate', help='If containers already exist, don\'t recreate them. ' +
                                                  'Incompatible with --force-recreate and -V.', action='store_true')
        parser.add_argument('--force-recreate', help='Recreate containers even if their ' +
                                                     'configuration and image haven\'t changed.', action='store_true')
        parser.add_argument('--no-build', help='Don\'t build an image, even if it\'s missing.', action='store_true')
        parser.add_argument('--no-deps', help='Don\'t start linked services.', action='store_true')
        parser.add_argument('--no-detach', '-n', help='Don\'t start in detach mode', action='store_true')

    def get_name(self) -> str:
        return ':start'

    def run(self, context: ExecutionContext) -> bool:
        # @todo: Rewrite to use service.py
        return False


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
        parser.add_argument('--force-recreate', '-r', help='Force recreate', action='store_true')

    def run(self, context: ExecutionContext) -> bool:
        force_recreate = context.get_arg('--force-recreate')
        success = True

        self.io().h2('Pulling images')
        self.rkd([':harbor:pull', '--profile=%s' % context.get_arg('--profile')])

        for service in self.get_matching_services(context):
            self.io().h2('Upgrading %s' % service.get_name())

            if force_recreate:
                try:
                    self.rkd([':harbor:service:rm', '--name=%s' % service.get_name()])
                except CalledProcessError:
                    pass

            try:
                self.rkd([':harbor:service:up', '--name=%s' % service.get_name()])
            except CalledProcessError:
                success = False

        self.rkd([':harbor:gateway:update'])

        return success
