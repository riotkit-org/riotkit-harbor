import unittest
import os
from typing import Dict
from copy import deepcopy
from argparse import ArgumentParser
from rkd.contract import ExecutionContext
from rkd.context import ApplicationContext
from rkd.executor import OneByOneTaskExecutor
from rkd.inputoutput import IO
from rkd.inputoutput import BufferedSystemIO
from rkd.syntax import TaskDeclaration
from .tasks.base import HarborBaseTask
from .service import ServiceDeclaration
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

    def _get_prepared_compose_driver(self, args: dict = {}, env: dict = {}) -> ComposeDriver:
        merged_env = deepcopy(os.environ)
        merged_env.update(env)

        task = create_mocked_task(BufferedSystemIO())
        declaration = TaskDeclaration(task)
        ctx = ExecutionContext(declaration, args=args, env=merged_env)

        return ComposeDriver(task, ctx, 'test')

    def prepare_example_service(self, name: str) -> ComposeDriver:
        drv = self._get_prepared_compose_driver()

        # prepare
        drv.rm(ServiceDeclaration(name, {}))
        drv.up(ServiceDeclaration(name, {}))

        return drv

    def get_containers_state(self, driver: ComposeDriver) -> Dict[str, bool]:
        running_rows = driver.scope.sh('docker ps -a --format "{{ .Names }}|{{ .Status }}"', capture=True).split("\n")
        containers = {}

        for container_row in running_rows:
            try:
                name, status = container_row.split('|')
            except ValueError:
                continue

            if name.startswith(driver.project_name + '_'):
                containers[name] = 'Up' in status

        return containers

