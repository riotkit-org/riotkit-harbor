
import os
import json
from traceback import format_exc
from subprocess import CalledProcessError
from typing import Optional
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from .base import HarborBaseTask
from ..formatting import prod_formatting


class BaseRepositoryTask(HarborBaseTask):
    def get_group_name(self) -> str:
        return ':harbor:git:apps'

    def format_task_name(self, name) -> str:
        return prod_formatting(name)

    def get_app_repository_path(self, app_name: str, context: ExecutionContext) -> Optional[str]:
        return self.get_apps_path(context) + '/repos-enabled/%s.sh' % app_name

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('name', help='Application name (based on data/repos-enabled/*.sh)')

    def contextual_sh(self, path: str, script: str, capture: bool = False):
        """Adds a context of pre/post hooks and configuration"""

        return self.sh(
            '''
                current_pwd=$(pwd);

                # define hooks to override
                pre_update() { return 0; }
                post_update() { return 0; }

                source ''' + path + ''';

                ''' + script + '''
            ''',
            capture=capture
        )

    @staticmethod
    def _get_var(project_vars: dict, path: str, var_name: str):
        if var_name not in project_vars:
            raise Exception('%s is not defined in %s, as well as in %s' % (var_name, path, '.env'))

        return project_vars[var_name]

    def _load_project_vars(self, path: str):
        return json.loads(
            self.contextual_sh(path, 'python3 -c "import json; import os; print(json.dumps(dict(os.environ)))"',
                               capture=True)
        )

    def list_repositories(self, context: ExecutionContext) -> list:
        path = self.get_apps_path(context) + '/repos-enabled'
        names = []

        for file in os.scandir(path):
            file: os.DirEntry

            if not file.name.endswith('.sh'):
                continue

            names.append(file.name[:-3])

        names.sort()

        return names

    def _get_permissions_command(self):
        return 'sudo -E -u %s ' % self.app_user


class FetchRepositoryTask(BaseRepositoryTask):
    """Fetch a git repository from the remote"""

    def get_name(self) -> str:
        return ':update'

    def run(self, context: ExecutionContext) -> bool:
        path = self.get_app_repository_path(context.get_arg('name'), context)

        if not os.path.isfile(path):
            self.io().error_msg('Cannot pull a repository: Unknown application, "%s" file not found' % path)
            return False

        # load variables from shell into our current Python context
        project_vars = self._load_project_vars(path)

        project_root_path = self.get_apps_path(context) + '/www-data/' + self._get_var(
            project_vars, path, 'GIT_PROJECT_DIR')

        # 1) run pre_update hook
        self.contextual_sh(path, 'pre_update %s' % project_root_path)

        # 2a) clone fresh repository
        if not os.path.isdir(project_root_path):
            self.io().info('Cloning a fresh repository at "%s"' % project_root_path)

            self._clone_new_repository(path, project_vars)

        # 2b) update existing repository - pull changes
        else:
            self.io().info('Pulling in an existing repository at "%s"' % project_root_path)
            self._pull_changes_into_existing_repository(path, project_vars)

        # 3) run pre_update hook
        self.contextual_sh(path, 'post_update %s' % project_root_path)

        self.io().print_opt_line()
        self.io().success_msg('Application\'s repository updated.')

        return True

    def _pull_changes_into_existing_repository(self, config_path: str, project_vars):
        """Updates existing local repository with remote changes"""

        # pass variables from Python to early-validate instead of throwing bash undeclared-var errors
        git_proto = self._get_var(project_vars, config_path, 'GIT_PROTO')
        git_project_dir = self._get_var(project_vars, config_path, 'GIT_PROJECT_DIR')
        git_user = self._get_var(project_vars, config_path, 'GIT_USER')
        git_server = self._get_var(project_vars, config_path, 'GIT_SERVER')
        git_password = self._get_var(project_vars, config_path, 'GIT_PASSWORD')
        git_org_name = self._get_var(project_vars, config_path, 'GIT_ORG_NAME')
        git_project_name = self._get_var(project_vars, config_path, 'GIT_PROJECT_NAME')

        command = '''
                set -e
                cd "./apps/www-data/''' + git_project_dir + '''"
    
                echo " >> Setting remote origin"
                %sudo% git config pull.rebase false
                %sudo% git remote remove origin 2>/dev/null || true
                %sudo% git remote add origin ''' + git_proto + '''://''' + git_user + ''':''' + git_password + '''@''' + git_server + '''/''' + git_org_name + '''/''' + git_project_name + '''
                %sudo% git pull origin master
                %sudo% git remote remove origin 2>/dev/null || true

            '''

        return self.contextual_sh(
            config_path,
            command.replace('%sudo%', self._get_permissions_command())
        )

    def _clone_new_repository(self, config_path: str, project_vars: dict):
        """Clones a new repository"""

        # pass variables from Python to early-validate instead of throwing bash undeclared-var errors
        git_proto = self._get_var(project_vars, config_path, 'GIT_PROTO')
        git_project_dir = self._get_var(project_vars, config_path, 'GIT_PROJECT_DIR')
        git_user = self._get_var(project_vars, config_path, 'GIT_USER')
        git_server = self._get_var(project_vars, config_path, 'GIT_SERVER')
        git_password = self._get_var(project_vars, config_path, 'GIT_PASSWORD')
        git_org_name = self._get_var(project_vars, config_path, 'GIT_ORG_NAME')
        git_project_name = self._get_var(project_vars, config_path, 'GIT_PROJECT_NAME')

        full_project_dir = os.path.realpath('./apps/www-data') + '/' + git_project_dir

        command = '''
                %sudo% git clone ''' + git_proto + '''://''' + git_user + ''':''' + git_password + '''@''' + git_server + '''/''' + git_org_name + '''/''' + git_project_name + ''' \
                    ''' + full_project_dir + ''' 
            '''

        command = command.replace('%sudo%', self._get_permissions_command())

        return self.contextual_sh(
            config_path,
            command
        )


class SetPermissionsForWritableDirectoriesTask(BaseRepositoryTask):
    """Make sure that the application would be able to write to allowed directories (eg. upload directories)"""

    def get_name(self) -> str:
        return ':set-permissions'

    def run(self, context: ExecutionContext) -> bool:
        path = self.get_app_repository_path(context.get_arg('name'), context)

        if not os.path.isfile(path):
            self.io().error_msg('Cannot pull a repository: Unknown application, "%s" file not found' % path)
            return False

        # load variables from shell into our current Python context
        project_vars = self._load_project_vars(path)

        writable_dirs = self._get_var(project_vars, path, 'WRITABLE_DIRS').replace('\\ ', '@SPACE@').split(' ')
        project_root_path = self.get_apps_path(context) + '/www-data/' + self._get_var(
            project_vars, path, 'GIT_PROJECT_DIR')
        container_user = self._get_var(project_vars, path, 'DEFAULT_CONTAINER_USER')

        for writable_dir in writable_dirs:
            writable_dir = writable_dir.replace('@SPACE@', ' ')

            command = 'sudo chown %s "%s/%s"' % (container_user, project_root_path, writable_dir)

            self.io().info(command)
            self.sh(command)

        return True


class ListRepositoriesTask(BaseRepositoryTask):
    """List GIT repositories"""

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_name(self) -> str:
        return ':list'

    def run(self, context: ExecutionContext) -> bool:
        header = ['Configured GIT repository']
        body = []

        for name in self.list_repositories(context):
            body.append([name])

        self.io().outln(self.table(header=header, body=body))

        return True


class FetchAllRepositories(BaseRepositoryTask):
    """List GIT repositories

    Ignores intermediate errors. When at least one repository fails to update,
    then overall status would be a failure.
    """

    def configure_argparse(self, parser: ArgumentParser):
        pass

    def get_name(self) -> str:
        return ':update-all'

    def run(self, context: ExecutionContext) -> bool:
        self.io().info('Fetching all repositories...')

        result = True

        with self.hooks_executed(context, 'repositories-upgrade'):
            for name in self.list_repositories(context):
                self.io().info('Updating "%s"' % name)

                try:
                    self.rkd([':harbor:git:apps:update', name])

                except CalledProcessError:
                    self.io().err(format_exc())
                    self.io().error_msg('Failed updating "%s"' % name)
                    result = False

        return result
