
from rkd.exception import TaskException


class ProfileNotFoundException(TaskException):
    def __init__(self, path: str):
        super().__init__('"%s" profile not found' % path)
