
"""Services declarations operations - docker-compose YAML represented as model
"""

import os
from typing import List
from typing import Optional
from typing import Dict
from traceback import format_exc
from rkd.api.inputoutput import IO
from .expressions import safe_eval
from .exception import ProfileNotFoundException
from .exception import ServiceNotFoundInYaml
from .exception import ServiceNotFoundInYamlLookedByCriteria

DEFAULT_SELECTOR = 'service is not None'  # passes all containers
BOOLEANS = ['true', 'TRUE', 'True', True]


class ServiceDeclaration(object):
    """Model of a parsed service declaration from YAML"""

    _name: str
    _definition: dict

    def __init__(self, name: str, definition: dict):
        self._name = name
        self._definition = definition

    def get_name(self) -> str:
        return self._name

    def get_definition(self) -> dict:
        return self._definition

    def get_domains(self) -> list:
        try:
            return str(self.get_definition()['environment']['VIRTUAL_HOST']).split(',')
        except KeyError:
            return []

    def is_using_watchtower(self) -> bool:
        try:
            return self.get_definition()['labels']['com.centurylinklabs.watchtower.enable'] in BOOLEANS
        except KeyError:
            return False

    def is_using_maintenance_mode(self) -> bool:
        try:
            return self.get_definition()['labels']['org.riotkit.useMaintenanceMode'] in BOOLEANS
        except KeyError:
            return False

    def get_ports(self) -> list:
        try:
            return self.get_definition()['ports']
        except KeyError:
            return []

    def get_desired_replicas_count(self) -> int:
        try:
            return int(self.get_definition()['labels']['org.riotkit.replicas'])
        except KeyError:
            return 1

    def get_update_strategy(self, default: str = 'compose') -> str:
        try:
            return str(self.get_definition()['labels']['org.riotkit.updateStrategy'])
        except KeyError:
            return default

    def get_priority_number(self):
        try:
            return int(self.get_definition()['labels']['org.riotkit.priority'])
        except KeyError:
            return 1000

    def get_image(self):
        try:
            return str(self.get_definition()['image'])
        except KeyError:
            return '_docker_build_local:latest'

    def get_declared_version(self):
        try:
            return str(self.get_definition()['image'].split(':')[1])
        except KeyError:
            return 'latest (build)'
        except IndexError:
            return 'latest'

    def has_domain(self, domain: str):
        return domain in self.get_domains()


class ServiceSelector(object):
    """Acts as a service filter. Simple reduce() implementation"""

    _selector: str
    _io: IO

    def __init__(self, selector: str, io: IO):
        self._selector = selector
        self._io = io

    def is_service_matching(self, definition: dict, name: str) -> bool:
        """Asks the profile filter - is service of a given definition and name matching?"""

        try:
            return safe_eval(self._selector, {'service': definition, 'name': name})
        except Exception:
            self._io.errln(format_exc())
            self._io.error_msg('Exception raised, while attempting to evaluate --profile selector')
            return False

    def find_matching_services(self, services: dict) -> List[ServiceDeclaration]:
        """Find names of matching services by current Service Selector"""
        matched = []

        for name, definition in services.items():
            if self.is_service_matching(definition, name):
                matched.append(ServiceDeclaration(name, definition))

        matched.sort(key=lambda declaration: declaration.get_priority_number())

        return matched


class ProfileLoader(object):
    """Parses profiles from ./apps/profiles
    """

    _io: IO
    _apps_path: str

    def __init__(self, io: IO, apps_path: str):
        self._io = io
        self._apps_path = apps_path

    def load_profile(self, name: str) -> ServiceSelector:
        if name == '' or name is None:
            return ServiceSelector(DEFAULT_SELECTOR, self._io)

        profile_path = self._apps_path + '/profile/%s.profile.py' % name

        if not os.path.isfile(profile_path):
            raise ProfileNotFoundException(profile_path)

        return self.load_profile_from_path(profile_path)

    def load_profile_from_path(self, path: str) -> ServiceSelector:
        with open(path, 'r') as f:
            content = f.read()

            return ServiceSelector(content, self._io)


class ServiceLocator(object):
    """Declarations repository"""

    _services: Dict[str, ServiceDeclaration]

    def __init__(self, services: dict):
        self._services = {}

        for name, yaml_dict in services.items():
            self._services[name] = ServiceDeclaration(name, yaml_dict)

    def get_by_name(self, name: str) -> Optional[ServiceDeclaration]:
        try:
            return self._services[name]
        except KeyError:
            raise ServiceNotFoundInYaml(name)

    def find_by_domain(self, domain: str) -> Optional[ServiceDeclaration]:
        for service in self._services.values():
            if service.has_domain(domain):
                return service

        raise ServiceNotFoundInYamlLookedByCriteria('has domain "%s"' % domain)
