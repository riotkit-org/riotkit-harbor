from rkd.syntax import TaskDeclaration
from .running import ListContainersTask
from .running import StartTask
from .running import ListDefinedServices


def imports():
    return [
        TaskDeclaration(ListContainersTask()),
        TaskDeclaration(StartTask()),
        TaskDeclaration(ListDefinedServices())
    ]
