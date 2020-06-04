
from rkd.exception import TaskException


class ProfileNotFoundException(TaskException):
    def __init__(self, path: str):
        super().__init__('"%s" profile not found' % path)


class ServiceNotFoundInYaml(TaskException):
    def __init__(self, name: str):
        super().__init__('Service "%s" not found in any of loaded docker-compose YAMLs' % name)
