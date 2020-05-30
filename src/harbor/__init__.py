from rkd.syntax import TaskDeclaration
from .tasks.running import ListContainersTask
from .tasks.running import StartTask
from .tasks.running import StopTask
from .tasks.running import StopAndRemoveTask
from .tasks.running import RestartTask
from .tasks.listing import ListDefinedServices
from .tasks.env import GetEnvTask
from .tasks.env import SetEnvTask


def imports():
    return [
        TaskDeclaration(ListContainersTask()),
        TaskDeclaration(StartTask()),
        TaskDeclaration(ListDefinedServices()),
        TaskDeclaration(StopTask()),
        TaskDeclaration(StopAndRemoveTask()),
        TaskDeclaration(RestartTask()),
        TaskDeclaration(GetEnvTask()),
        TaskDeclaration(SetEnvTask())
    ]
