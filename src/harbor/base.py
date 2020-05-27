
import os
import yaml
from abc import ABC
from abc import abstractmethod
from typing import Optional
from typing import Dict
from rkd.contract import TaskInterface
from rkd.contract import ExecutionContext
from .profile import ProfileLoader
from .cached_loader import CachedLoader

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class HarborBaseTask(TaskInterface, ABC):
    _compose_args: str

    def _build_compose_files_list(self, src_root: str, is_dev: bool) -> list:
        """Lists all YAML files to include in docker-compose arguments
        """

        yamls = {
            'conf': ['docker-compose.yml'],
            'conf.dev': []
        }

        for env_type in yamls.keys():
            for root, subdirs, files in os.walk(src_root + '/' + env_type):
                for file in files:
                    if not file.endswith('.yml') and not file.endswith('.yaml'):
                        continue

                    yamls[env_type].append(root + '/' + file)

        if is_dev:
            return yamls['conf'] + yamls['conf.dev']

        return yamls['conf']

    def _build_compose_arguments(self, src_root: str, project_name: str, is_dev: bool) -> str:
        """Internal method: Builds list of docker-compose arguments
        """

        yamls = self._build_compose_files_list(src_root, is_dev)
        args = ' -p %s ' % project_name

        for yaml_path in yamls:
            args += ' -f %s ' % yaml_path

        return args

    @staticmethod
    def _validate_env_present() -> bool:
        return os.path.isfile('./.env')

    def get_group_name(self) -> str:
        return ':harbor'

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'APPS_PATH': './apps/',
            'COMPOSE_PROJECT_NAME': None
        }

    @staticmethod
    def get_apps_path(ctx: ExecutionContext):
        return ctx.get_env('APPS_PATH')

    def profile_loader(self, ctx: ExecutionContext) -> ProfileLoader:
        """Loads profile of a ServiceSelector to filter out"""

        return ProfileLoader(self.io(), self.get_apps_path(ctx))

    def get_compose_yaml_as_dict(self):
        """Return's parsed docker-compose file as one big dictionary"""

        return CachedLoader.load_compose_definition(
            lambda: yaml.load(self.compose(['config'], capture=True), yaml.FullLoader)
        )

    def get_services(self):
        """Gets services from YAMLS"""
        parsed = self.get_compose_yaml_as_dict()

        return parsed['services'] if 'services' in parsed else {}

    @abstractmethod
    def run(self, context: ExecutionContext) -> bool:
        """Method to implement the proper logic of the task (instead of execute())
        """
        pass

    def execute(self, context: ExecutionContext) -> bool:
        """Harbor's wrapper - adds Harbor specific behavior before each task - initialization of the context
        """

        if not self._validate_env_present():
            self.io().error_msg('Missing .env file')
            return False

        project_name = context.get_env('COMPOSE_PROJECT_NAME')

        if not project_name:
            self.io().error_msg('COMPOSE_PROJECT_NAME environment variable is not defined, cannot proceed')
            return False

        self._compose_args = self._build_compose_arguments(
            context.get_env('APPS_PATH'),
            project_name,
            is_dev=True
        )

        self.io().debug('Compose args: %s' % self._compose_args)

        return self.run(context)

    def compose(self, arguments: list, capture: bool = False) -> Optional[str]:
        """Makes a call to docker-compose with all prepared arguments that should be"""

        cmd = 'docker-compose %s %s' % (self._compose_args, ' '.join(arguments))
        self.io().debug('Calling compose: %s' % cmd)

        return self.sh(cmd, capture=capture)
