import os
from rkd.syntax import TaskDeclaration
from rkd import main as rkd_main
from rkd.standardlib.env import GetEnvTask
from rkd.standardlib.env import SetEnvTask
from .tasks.running import ListContainersTask
from .tasks.running import StartTask
from .tasks.running import StopTask
from .tasks.running import StopAndRemoveTask
from .tasks.running import RestartTask
from .tasks.running import PullTask
from .tasks.service import ServiceRemoveTask
from .tasks.service import ServiceUpTask
from .tasks.service import ServiceDownTask
from .tasks.listing import ListDefinedServices
from .tasks.gateway import ReloadGatewayTask
from .tasks.gateway import ShowSSLStatusTask
from .tasks.gateway import ForceReloadSSLTask
from .tasks.configsmanagement import ListConfigsTask
from .tasks.configsmanagement import EnableConfigTask
from .tasks.configsmanagement import DisableConfigTask
from .tasks.maintenance import MaintenanceOnTask
from .tasks.maintenance import MaintenanceOffTask


def imports():
    return [
        TaskDeclaration(ListContainersTask()),
        TaskDeclaration(StartTask()),
        TaskDeclaration(StopTask()),
        TaskDeclaration(StopAndRemoveTask()),
        TaskDeclaration(ListDefinedServices()),
        TaskDeclaration(ServiceUpTask()),
        TaskDeclaration(ServiceDownTask()),
        TaskDeclaration(ServiceRemoveTask()),
        TaskDeclaration(PullTask()),
        TaskDeclaration(RestartTask()),
        TaskDeclaration(ListConfigsTask()),
        TaskDeclaration(EnableConfigTask()),
        TaskDeclaration(DisableConfigTask()),

        # production-related
        TaskDeclaration(ReloadGatewayTask()),
        TaskDeclaration(ShowSSLStatusTask()),
        TaskDeclaration(ForceReloadSSLTask()),
        TaskDeclaration(MaintenanceOnTask()),
        TaskDeclaration(MaintenanceOffTask()),

        TaskDeclaration(GetEnvTask()),
        TaskDeclaration(SetEnvTask())
    ]


def main():
    os.environ['RKD_WHITELIST_GROUPS'] = ':env,:harbor,'
    os.environ['RKD_ALIAS_GROUPS'] = '->:harbor'
    rkd_main()


if __name__ == '__main__':
    main()
