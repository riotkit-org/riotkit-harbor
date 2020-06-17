
from abc import ABC

from rkd.contract import TaskInterface


class HarborTaskInterface(TaskInterface, ABC):
    is_dev_env: bool
