from argparse import ArgumentParser
from typing import Dict
from rkd.contract import ExecutionContext
from .base import HarborBaseTask


class GatewayBaseTask(HarborBaseTask):
    def configure_argparse(self, parser: ArgumentParser):
        super().configure_argparse(parser)

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super().get_declared_envs()
        envs.update({
            'DISABLE_SSL': 'False'
        })

        return envs

    def make_sure_ssl_service_is_up(self, ctx: ExecutionContext):
        service = self.services(ctx).get_by_name('gateway_letsencrypt')

        self.containers(ctx).up(service, norecreate=True)
        self.containers(ctx).wait_for_log_message('Sleep for', service, timeout=60)


class ReloadGatewayTask(GatewayBaseTask):
    """Reload gateway, regenerate missing SSL certificates"""

    def run(self, ctx: ExecutionContext) -> bool:
        self.io().h2('Validating NGINX configuration')
        self.containers(ctx).exec_in_container('gateway', 'nginx -t')

        self.io().h2('Reloading NGINX configuration')
        self.containers(ctx).exec_in_container('gateway', 'nginx -s reload')

        if ctx.get_env('DISABLE_SSL').lower() != 'true':
            self.io().h2('Reloading SSL configuration')
            self.make_sure_ssl_service_is_up(ctx)
            self.containers(ctx).exec_in_container('gateway_letsencrypt', '/app/signal_le_service')

        return True

    def get_name(self) -> str:
        return ':reload'

    def get_group_name(self) -> str:
        return ':harbor:prod:gateway'


class ShowSSLStatusTask(GatewayBaseTask):
    """Show status of SSL certificates"""

    def run(self, ctx: ExecutionContext) -> bool:
        if ctx.get_env('DISABLE_SSL').lower() != 'true':
            self.make_sure_ssl_service_is_up(ctx)
            self.io().out(self.containers(ctx).exec_in_container('gateway_letsencrypt', '/app/cert_status'))

        return True

    def get_name(self) -> str:
        return ':status'

    def get_group_name(self) -> str:
        return ':harbor:prod:gateway:ssl'


class ForceReloadSSLTask(GatewayBaseTask):
    """Regenerate all certificates with force"""

    def run(self, ctx: ExecutionContext) -> bool:
        if ctx.get_env('DISABLE_SSL').lower() != 'true':
            self.make_sure_ssl_service_is_up(ctx)
            self.io().out(self.containers(ctx).exec_in_container('gateway_letsencrypt', '/app/force_renew'))

        return True

    def get_name(self) -> str:
        return ':regenerate'

    def get_group_name(self) -> str:
        return ':harbor:prod:gateway:ssl'
