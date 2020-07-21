
from rkd.exception import TaskException


class ProfileNotFoundException(TaskException):
    def __init__(self, path: str):
        super().__init__('"%s" profile not found' % path)


class ServiceNotFoundInYaml(TaskException):
    def __init__(self, name: str):
        super().__init__('Service "%s" not found in any of loaded docker-compose YAMLs' % name)


class ServiceNotFoundInYamlLookedByCriteria(TaskException):
    def __init__(self, criteria: str):
        super().__init__('No any service found matching those criteria: %s' % criteria)


class ServiceNotCreatedException(TaskException):
    def __init__(self, name: str, instance_num: int = None):
        super().__init__('Service "%s" (instance=%s) was not yet created by docker engine, please start it first' % (
            name, str(instance_num)
        ))


class ServiceNotRunningException(TaskException):
    def __init__(self, name: str, instance_num='last'):
        super().__init__('Service "%s" seems to be not running, at least at instance #%s' % (name, instance_num))


class ServiceNotReadyException(TaskException):
    def __init__(self, name: str, text: str, instance_num='last'):
        super().__init__('Service "%s" #%s is not ready yet. "%s" text not found in logs' % (
            name, instance_num, text
        ))


class DeploymentException(TaskException):
    pass


class MissingDeploymentConfigurationError(TaskException):
    def __init__(self):
        super().__init__('Deployment not configured - missing deployment.yml or deployment.yaml file')
