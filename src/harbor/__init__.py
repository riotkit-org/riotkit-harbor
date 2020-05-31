from rkd.syntax import TaskDeclaration
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
from .tasks.env import GetEnvTask
from .tasks.env import SetEnvTask


def imports():
    return [
        TaskDeclaration(ListContainersTask()),
        TaskDeclaration(StartTask()),
        TaskDeclaration(ListDefinedServices()),
        TaskDeclaration(ServiceUpTask()),
        TaskDeclaration(ServiceDownTask()),
        TaskDeclaration(ServiceRemoveTask()),
        TaskDeclaration(StopTask()),
        TaskDeclaration(StopAndRemoveTask()),
        TaskDeclaration(PullTask()),
        TaskDeclaration(RestartTask()),
        TaskDeclaration(ReloadGatewayTask()),
        TaskDeclaration(ShowSSLStatusTask()),
        TaskDeclaration(ForceReloadSSLTask()),
        TaskDeclaration(GetEnvTask()),
        TaskDeclaration(SetEnvTask())
    ]
