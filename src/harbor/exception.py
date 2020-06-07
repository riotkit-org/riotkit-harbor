
from rkd.exception import TaskException


class ProfileNotFoundException(TaskException):
    def __init__(self, path: str):
        super().__init__('"%s" profile not found' % path)


class ServiceNotFoundInYaml(TaskException):
    def __init__(self, name: str):
        super().__init__('Service "%s" not found in any of loaded docker-compose YAMLs' % name)


class ServiceNotCreatedException(TaskException):
    def __init__(self, name: str):
        super().__init__('Service "%s" was not yet created by docker engine, please start it first' % name)


class ServiceNotRunningException(TaskException):
    def __init__(self, name: str, instance_num='last'):
        super().__init__('Service "%s" seems to be not running, at least at instance #%s' % (name, instance_num))


class ServiceNotReadyException(TaskException):
    def __init__(self, name: str, text: str, instance_num='last'):
        super().__init__('Service "%s" #%s is not ready yet. "%s" text not found in logs' % (
            name, instance_num, text
        ))
