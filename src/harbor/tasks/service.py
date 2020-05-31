from argparse import ArgumentParser
from rkd.contract import ExecutionContext
from json import loads as json_loads
from .base import HarborBaseTask


class BaseHarborServiceTask(HarborBaseTask):
    """Abstract class"""

    def get_group_name(self) -> str:
        return ':harbor:service'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)

        parser.add_argument('--name', '-n', required=True, help='Service name')
        parser.add_argument('--compose-args', '-c', help='Optional compose arguments', default='')

    def inspect_service(self, name: str, ctx: ExecutionContext):
        container_name = self.get_container_name_for_service(name, ctx)
        out = self.sh('docker inspect %s' % container_name, capture=True)
        as_json = json_loads(out)

        if not as_json:
            raise Exception('Cannot inspect container, unknown docker inspect output: %s' % out)

        return as_json[0]


class ServiceUpTask(BaseHarborServiceTask):
    """Starts a single service
    """

    def get_name(self) -> str:
        return ':up'

    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)
        parser.add_argument('--dont-recreate', '-d', action='store_true', help='Don\'t recreate the container if' +
                                                                               ' already existing')

    def run(self, context: ExecutionContext) -> bool:
        service_name = context.get_arg('--name')
        recreate = '--no-recreate' if context.get_arg('--dont-recreate') else ''

        self.compose(['up', '-d', recreate, service_name, context.get_arg('--compose-args')])
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

    def run(self, context: ExecutionContext) -> bool:
        service_name = context.get_arg('--name')
        is_removing_image = context.get_arg('--with-image')
        img_to_remove = ''

        if is_removing_image:
            inspected = self.inspect_service(service_name, context)

            if inspected:
                img_to_remove = inspected['Image']

        self.compose(['rm', '--stop', '--force', service_name, context.get_arg('--compose-args')])

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
