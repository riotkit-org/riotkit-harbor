from argparse import ArgumentParser
from .base import HarborBaseTask
from rkd.api.contract import ExecutionContext


class DumpComposeArguments(HarborBaseTask):
    """Shows arguments that Harbor passes to docker-compose all the time"""

    def get_group_name(self) -> str:
        return ':harbor:diagnostic'

    def get_name(self) -> str:
        return ':dump-compose-args'

    def run(self, context: ExecutionContext) -> bool:
        try:
            self.io().outln(self.containers(context).get_compose_args())

        except AttributeError as e:
            self.io().error_msg('Cannot retrieve compose arguments, possibly not using docker-compose. ' +
                                'Details: %s' % str(e))
            return False

        return True


class ListContainersTask(HarborBaseTask):
    """List all containers
    """

    def get_group_name(self) -> str:
        return ':harbor:diagnostic:compose'

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


class DumpComposeConfigTask(HarborBaseTask):
    """Dump all compose YAMLs as one YAML"""

    def get_group_name(self) -> str:
        return ':harbor:diagnostic:compose'

    def get_name(self) -> str:
        return ':config'

    def run(self, context: ExecutionContext) -> bool:
        self.containers(context).compose(['config'])

        return True
