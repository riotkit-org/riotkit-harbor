import os
from typing import Optional
from argparse import ArgumentParser
from rkd.contract import TaskInterface
from rkd.contract import ExecutionContext


class GetEnvTask(TaskInterface):
    """Gets environment variable value"""

    def get_name(self) -> str:
        return ':get'

    def get_group_name(self) -> str:
        return ':env'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--name', '-e', help='Environment variable name', required=True)

    def execute(self, context: ExecutionContext) -> bool:
        self.io().out(os.getenv(context.get_arg('--name')))

        return True


class SetEnvTask(TaskInterface):
    """Sets environment variable in the .env file"""

    def get_name(self) -> str:
        return ':set'

    def get_group_name(self) -> str:
        return ':env'

    def configure_argparse(self, parser: ArgumentParser):
        parser.add_argument('--name', '-e', help='Environment variable name', required=True)
        parser.add_argument('--value', '-w', help='New value to set', required=False, default='')
        parser.add_argument('--ask', help='Ask for a value', required=False, action='store_true')
        parser.add_argument('--ask-text', help='Text to show, when asking for input', required=False, default='')

    def execute(self, context: ExecutionContext) -> bool:
        new_env_contents = ''
        env_name = context.get_arg('--name')
        new_value = context.get_arg('--value')
        path = os.getcwd() + '/.env'

        if context.get_arg('--ask'):
            txt = context.get_arg('--ask-text') if context.get_arg('--ask-text') else 'Please provide value for %s:' %\
                env_name
            new_value = input(txt + ' ')

        # write to existing file
        if os.path.isfile(path):
            wrote = False

            with open(path, 'r') as fo:
                for line in fo.readlines():
                    current_env_name = self.parse_env_name_from_line(line)

                    if current_env_name == env_name:
                        wrote = True
                        line = env_name + '=' + new_value + "\n"

                    new_env_contents += line

            if not wrote:
                new_env_contents += env_name + '=' + new_value + "\n"

        # create a new file
        else:
            new_env_contents += env_name + '=' + new_value + "\n"

        with open(path, 'w') as wo:
            wo.write(new_env_contents)

        return True

    @staticmethod
    def parse_env_name_from_line(line: str) -> Optional[str]:
        if "=" not in line:
            return None

        parts = line.split('=')

        # it may be a comment for example
        if ' ' in parts[0] or parts[0][0] == '#':
            return None

        return parts[0]
