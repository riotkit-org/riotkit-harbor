
import os
import yaml
import pkg_resources
from contextlib import contextmanager
from subprocess import check_output
from argparse import ArgumentParser
from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import List
from enum import Enum
from rkd.api.contract import ExecutionContext
from ..service import ProfileLoader
from ..service import ServiceDeclaration
from ..service import ServiceLocator
from ..driver import ComposeDriver
from ..cached_loader import CachedLoader
from ..interface import HarborTaskInterface

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class UpdateStrategy(Enum):
    rolling = 'rolling'
    recreate = 'recreate'
    compose = 'compose'
    auto = 'auto'

    def __str__(self):
        return self.value


class HarborBaseTask(HarborTaskInterface):
    _compose_args: str
    is_dev_env: bool
    app_user: str
    app_group_id: int

    #
    # TaskInterface
    #
    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_group_name(self) -> str:
        return ':harbor'

    def get_declared_envs(self) -> Dict[str, str]:
        return {
            'APPS_PATH': './apps/',
            'HOOKS_PATH': './hooks.d/',
            'DATA_PATH': './data/',
            'COMPOSE_PROJECT_NAME': None,
            'DOMAIN_SUFFIX': ''
        }

    #
    # Lazy-dependencies
    #
    def services(self, ctx: ExecutionContext) -> ServiceLocator:
        return CachedLoader.cached('services', lambda: ServiceLocator(self.get_services_as_raw_dict(ctx)))

    def containers(self, ctx: ExecutionContext) -> ComposeDriver:
        return CachedLoader.cached('containers',
                                   lambda: ComposeDriver(self, ctx, self.get_project_name(ctx)))

    def profile_loader(self, ctx: ExecutionContext) -> ProfileLoader:
        """Loads profile of a ServiceSelector to filter out"""

        return ProfileLoader(self.io(), self.get_apps_path(ctx))

    #
    # Validation
    #
    @staticmethod
    def _validate_env_present() -> bool:
        return os.path.isfile('./.env')

    #
    # Configuration
    #
    @staticmethod
    def get_apps_path(ctx: ExecutionContext) -> str:
        return ctx.get_env('APPS_PATH')

    @staticmethod
    def get_hooks_dir(ctx: ExecutionContext) -> str:
        return ctx.get_env('HOOKS_PATH')

    @staticmethod
    def get_data_path(ctx: ExecutionContext) -> str:
        return ctx.get_env('DATA_PATH')

    @staticmethod
    def get_project_name(ctx: ExecutionContext) -> str:
        return ctx.get_env('COMPOSE_PROJECT_NAME')

    def get_compose_yaml_as_dict(self, ctx: ExecutionContext):
        """Return's parsed docker-compose file as one big dictionary"""

        return CachedLoader.load_compose_definition(
            lambda: yaml.load(self.containers(ctx).compose(['config'], capture=True), yaml.Loader)
        )

    def get_services_as_raw_dict(self, ctx: ExecutionContext):
        """Gets services from YAMLS"""
        parsed = self.get_compose_yaml_as_dict(ctx)

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

        self.app_user, self.app_group_id = self.detect_repository_owning_user_and_group()
        self.is_dev_env = self.detect_dev_env(context)
        project_name = context.get_env('COMPOSE_PROJECT_NAME')

        # project directory has to have owner that will manage files, that should be a deployment user
        self.io().debug('Project owner: USER=%s, GID=%i' % (self.app_user, self.app_group_id))

        if not project_name:
            self.io().error_msg('COMPOSE_PROJECT_NAME environment variable is not defined, cannot proceed')
            return False

        return self.run(context)

    @staticmethod
    def detect_repository_owning_user_and_group() -> tuple:
        """Detects user and group that should be owner of the project repository"""

        usr = os.getenv('APP_USER', '')
        grp = os.getenv('APP_GROUP_ID', '')

        if not usr and os.getenv('SUDO_USER'):
            usr = os.getenv('SUDO_USER')

        if not grp and os.getenv('SUDO_GID'):
            grp = os.getenv('SUDO_GID')

        if not usr:
            usr = os.getenv('USER')

        if not grp:
            grp = check_output(['id', '-g', usr]).decode('utf-8').strip()

        return usr, int(grp)

    @staticmethod
    def detect_dev_env(context: ExecutionContext) -> bool:
        suffix = context.get_env('DOMAIN_SUFFIX')

        return suffix.endswith('.localhost') or suffix.endswith('.xip.io')

    @contextmanager
    def hooks_executed(self, ctx: ExecutionContext, hooks_suffix: str):
        self.execute_hooks(ctx, 'pre-' + hooks_suffix)
        yield
        self.execute_hooks(ctx, 'post-' + hooks_suffix)

    def execute_hooks(self, ctx: ExecutionContext, hook_name: str):
        """Executes a hooks from directory "hooks.d", when any executed script will fail, then an exception is raised

        The error handling must be implemented in the scripts itself
        """

        hooks_dir = self.get_hooks_dir(ctx) + '/' + hook_name + '/'

        if not os.path.isdir(hooks_dir):
            self.io().debug('Hooks dir "%s" not present, skipping' % hooks_dir)
            return

        self.io().info('Executing hook scripts for action "%s"' % hook_name)

        for script in os.scandir(hooks_dir):
            script: os.DirEntry

            if script.name.split('.')[0] == '':
                continue

            self.io().info('Running hook script "%s"' % script.path)

            try:
                self.sh(script.path)
            except Exception as e:
                self.io().error_msg('Failed executing script: "%s"' % script.path)
                raise e

    def get_harbor_version(self) -> str:
        try:
            return pkg_resources.get_distribution("harbor").version
        except:
            return 'dev'

    def _silent_mkdir(self, path: str):
        try:
            os.mkdir(path)
        except FileExistsError:
            pass


class BaseProfileSupportingTask(HarborBaseTask, ABC):
    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--profile', '-p', help='Services profile', default='')

    def get_matching_services(self, ctx: ExecutionContext) -> List[ServiceDeclaration]:
        service_selector = self.profile_loader(ctx).load_profile(ctx.get_arg('--profile'))
        matched = service_selector.find_matching_services(self.get_services_as_raw_dict(ctx))

        return matched

    def get_matching_service_names(self, context: ExecutionContext) -> List[str]:
        service_names = []

        for service in self.get_matching_services(context):
            service_names.append(service.get_name())

        return service_names
