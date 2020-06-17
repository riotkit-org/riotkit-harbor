import unittest
import os
from copy import deepcopy
from argparse import ArgumentParser
from rkd.contract import ExecutionContext
from rkd.context import ApplicationContext
from rkd.executor import OneByOneTaskExecutor
from rkd.inputoutput import IO
from rkd.inputoutput import BufferedSystemIO
from rkd.syntax import TaskDeclaration
from .tasks.base import HarborBaseTask
from .driver import ComposeDriver


class TestTask(HarborBaseTask):
    is_dev_env = True

    def get_name(self) -> str:
        return ':test'

    def get_group_name(self) -> str:
        return ''

    def execute(self, context: ExecutionContext) -> bool:
        return True

    def run(self, context: ExecutionContext) -> bool:
        return True

    def configure_argparse(self, parser: ArgumentParser):
        pass


def create_mocked_task(io: IO) -> TestTask:
    task = TestTask()
    ctx = ApplicationContext([], [])
    ctx.io = io

    task.internal_inject_dependencies(
        io=io,
        ctx=ctx,
        executor=OneByOneTaskExecutor(ctx=ctx)
    )

    return task


class BaseHarborTestClass(unittest.TestCase):
    def setUp(self) -> None:
        os.environ['APPS_PATH'] = os.path.dirname(os.path.realpath(__file__)) + '/../../test/testdata/env_simple/apps'
        os.chdir(os.path.dirname(os.path.realpath(__file__)) + '/../../test/testdata/env_simple')

    def _get_mocked_compose_driver(self, args: dict = {}, env: dict = {}) -> ComposeDriver:
        merged_env = deepcopy(os.environ)
        merged_env.update(env)

        task = create_mocked_task(BufferedSystemIO())
        declaration = TaskDeclaration(task)
        ctx = ExecutionContext(declaration, args=args, env=merged_env)

        return ComposeDriver(task, ctx, 'test')
