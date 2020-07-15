import os
import subprocess
from json import loads as json_loads
from glob import glob
from argparse import ArgumentParser
from typing import Dict
from urllib.parse import urlparse
from rkd.contract import ExecutionContext
from rkd.exception import MissingInputException
from rkd.inputoutput import Wizard
from .base import HarborBaseTask
from ..formatting import development_formatting

HARBOR_PATH = os.path.dirname(os.path.realpath(__file__)) + '/..'
DEFAULT_REPOSITORIES = 'https://github.com/riotkit-org/riotkit-harbor-snippet-cooperative'
REPOSITORIES_DIRECTORY = '.rkd/cooperative'


class BaseCooperativeTask(HarborBaseTask):
    def format_task_name(self, name) -> str:
        return development_formatting(name)

    def get_declared_envs(self) -> Dict[str, str]:
        envs = super(BaseCooperativeTask, self).get_declared_envs()
        envs['REPOSITORIES'] = DEFAULT_REPOSITORIES

        return envs

    def get_group_name(self) -> str:
        return ':harbor:cooperative'

    def get_repositories_list(self, ctx: ExecutionContext) -> list:
        try:
            return ctx.get_arg_or_env('--repositories').split(',')
        except MissingInputException:
            return DEFAULT_REPOSITORIES.split(',')


class CooperativeSyncTask(BaseCooperativeTask):
    """Synchronize repositories of the RiotKit's Snippets Cooperative"""

    def get_name(self) -> str:
        return ':sync'

    def run(self, ctx: ExecutionContext) -> bool:
        end_result = True

        for repository in self.get_repositories_list(ctx):
            self.io().info('Syncing repository "%s"' % repository)

            if not self.sync_repository(repository):
                self.io().error('Failed to synchronize repository "%s"' % repository)

                end_result = False
                continue

            self.io().info('Repository synced.')

        return end_result

    def sync_repository(self, git_url: str):
        repository_dir = REPOSITORIES_DIRECTORY + '/' + self.extract_repository_name_from_git_url(git_url)

        try:
            if not os.path.isdir(repository_dir + '/'):
                self.sh(' '.join(['mkdir', '-p', repository_dir]))
                self.sh(' '.join(['git', 'clone', git_url, repository_dir]))
                return True

            # pull the existing repository
            self.sh('''cd "%s" && git reset --hard HEAD && git checkout master && git pull''' % repository_dir)

        except subprocess.CalledProcessError as e:
            self.io().error('Error fetching a git repository: %s' % str(e))
            return False

        return True

    @staticmethod
    def extract_repository_name_from_git_url(git_url: str) -> str:
        if git_url.startswith('http'):
            return urlparse('https://github.com/riotkit-org/riotkit-harbor-snippet-cooperative').path[1:]

        name = git_url[5:].split(':')[1]

        if name.endswith('.git'):
            return name[0:-4]

        return name


class CooperativeInstallTask(BaseCooperativeTask):
    """Installs a snippet from the previously synchronized repository"""

    def get_name(self) -> str:
        return ':install'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('name', help='Snippet name')

    def run(self, ctx: ExecutionContext) -> bool:
        name = ctx.get_arg('name')
        path = self.find_snippet_path(name)

        if not path:
            self.io().error('Snippet not found in any synchronized repository. ' +
                            'Did you forget to do harbor :harbor:cooperative:sync?')
            return False

        self.io().info('Installing snippet from "%s"' % path)

        # mock rkd_path, so the snippet can override the tasks
        rkd_path = os.getenv('rkd_path', '')
        snippet_rkd_path = os.path.realpath('./' + path + '/.rkd')

        if snippet_rkd_path:
            os.putenv('RKD_PATH', (snippet_rkd_path + ':' + rkd_path).strip(':'))

        try:
            subprocess.check_call(['rkd', ':snippet:wizard', path])
            subprocess.check_call(['rkd', ':snippet:install', path])
        finally:
            if os.path.isfile('.rkd/tmp-wizard.json'):
                os.unlink('.rkd/tmp-wizard.json')

            os.putenv('rkd_path', rkd_path)

        return True

    def find_snippet_path(self, name: str):
        """Finds a snippet path by name.

        Raises:
            Exception: When snippet exists in multiple repositories
        """

        found_path = None

        for snippet_path in self.list_snippets():
            snippet_name = os.path.basename(snippet_path)

            if snippet_name == name:
                if found_path is not None:
                    raise Exception('Ambiguous match, %s exists in %s and in %s' % (name, found_path, snippet_path))

                found_path = snippet_path

        return found_path

    @staticmethod
    def list_snippets():
        dirs = glob('.rkd/cooperative/**/**/files', recursive=True)

        return list(set(map(lambda name: os.path.dirname(name), dirs)))


class CooperativeSnippetWizardTask(BaseCooperativeTask):
    """Snippet wizard - to be overridden by custom task provided by snippet"""

    def run(self, context: ExecutionContext) -> bool:
        pass

    def get_group_name(self) -> str:
        return ':snippet'

    def get_name(self) -> str:
        return ':wizard'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('path', help='Path to the root directory of the snippet files')

    def execute(self, ctx: ExecutionContext) -> bool:
        return True


class CooperativeSnippetInstallTask(BaseCooperativeTask):
    """Snippet installation - to be overridden by custom task provided by snippet"""

    def run(self, context: ExecutionContext) -> bool:
        pass

    def get_group_name(self) -> str:
        return ':snippet'

    def get_name(self) -> str:
        return ':install'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('path', help='Path to the root directory of the snippet files')

    def execute(self, ctx: ExecutionContext) -> bool:
        wizard = Wizard(self)
        wizard.load_previously_stored_values()
        os.environ.update(wizard.answers)

        self.rkd([
            ':j2:directory-to-directory',
            '--source="%s"' % ctx.get_arg('path') + '/files/',
            '--target="./"',
            '--pattern="(.*)"'
        ])
        return True
