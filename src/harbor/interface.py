
from abc import ABC
from abc import abstractmethod
from typing import Optional

from rkd.contract import TaskInterface


class HarborTaskInterface(TaskInterface, ABC):

    @abstractmethod
    def compose(self, arguments: list, capture: bool = False) -> Optional[str]:
        pass

    @abstractmethod
    def exec_in_container(self, container_name: str, command: str) -> str:
        pass
