
import os
from traceback import print_exc
from typing import List
from rkd.inputoutput import IO
from .expressions import safe_eval
from .exception import ProfileNotFoundException

DEFAULT_SELECTOR = 'service is not None'  # passes all containers
BOOLEANS = ['true', 'TRUE', 'True', True]


class Service(object):
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


class ServiceSelector(object):
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
            print_exc()
            self._io.error_msg('Exception raised, while attempting to evaluate --profile selector')
            return False

    def find_matching_services(self, services: dict) -> List[Service]:
        """Find names of matching services by current Service Selector"""
        matched = []

        for name, definition in services.items():
            if self.is_service_matching(definition, name):
                matched.append(Service(name, definition))

        return matched


class ProfileLoader(object):
    """Parses profiles in ./apps/profiles
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
