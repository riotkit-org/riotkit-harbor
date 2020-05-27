from rkd.syntax import TaskDeclaration
from .tasks.running import ListContainersTask
from .tasks.running import StartTask
from .tasks.running import ListDefinedServices


def imports():
    return [
        TaskDeclaration(ListContainersTask()),
        TaskDeclaration(StartTask()),
        TaskDeclaration(ListDefinedServices())
    ]
