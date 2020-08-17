
from abc import ABC

from rkd.api.contract import TaskInterface


class HarborTaskInterface(TaskInterface, ABC):
    is_dev_env: bool
