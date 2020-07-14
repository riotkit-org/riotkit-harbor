import os
import subprocess
from typing import Dict
from urllib.parse import urlparse
from rkd.contract import ExecutionContext
from rkd.exception import MissingInputException
from .base import HarborBaseTask

HARBOR_PATH = os.path.dirname(os.path.realpath(__file__)) + '/..'
DEFAULT_REPOSITORIES = 'https://github.com/riotkit-org/riotkit-harbor-snippet-cooperative'
REPOSITORIES_DIRECTORY = '.rkd/cooperative'


class BaseCooperativeTask(HarborBaseTask):

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
            self.io().error('Error feching a git repository: %s' % str(e))
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
