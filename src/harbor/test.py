import unittest
import os
import subprocess
from io import StringIO
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
from dotenv import dotenv_values


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
        env_simple_path = os.path.dirname(os.path.realpath(__file__)) + '/../../test/testdata/env_simple'

        os.environ.update(dotenv_values(env_simple_path + '/.env'))
        os.environ['APPS_PATH'] = env_simple_path + '/apps'
        os.chdir(env_simple_path)

    def _get_prepared_compose_driver(self, args: dict = {}, env: dict = {}) -> ComposeDriver:
        merged_env = deepcopy(os.environ)
        merged_env.update(env)

        task = create_mocked_task(BufferedSystemIO())
        declaration = TaskDeclaration(task)
        ctx = ExecutionContext(declaration, args=args, env=merged_env)

        return ComposeDriver(task, ctx, 'test')

    def execute_task(self, task: HarborBaseTask, args: dict = {}, env: dict = {}, debug: bool = False) -> str:
        ctx = ApplicationContext([], [])
        ctx.io = BufferedSystemIO()

        task.internal_inject_dependencies(
            io=ctx.io,
            ctx=ctx,
            executor=OneByOneTaskExecutor(ctx=ctx)
        )

        merged_env = deepcopy(os.environ)
        merged_env.update(env)

        r_io = IO()
        str_io = StringIO()

        with r_io.capture_descriptors(enable_standard_out=debug, stream=str_io):
            task.execute(ExecutionContext(
                TaskDeclaration(task),
                args=args,
                env=merged_env
            ))

        return ctx.io.get_value() + "\n" + str_io.getvalue()

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

    def get_locally_pulled_docker_images(self) -> list:
        images = subprocess.check_output(['docker', 'images', '--format', '{{ .Repository }}:{{ .Tag }}'])\
            .decode('utf-8')\
            .split("\n")

        return images

    def assertContainerIsNotRunning(self, service_name: str, driver: ComposeDriver):
        container_name_without_instance_num = driver.project_name + '_' + service_name + '_'

        for name, state in self.get_containers_state(driver).items():
            if name.startswith(container_name_without_instance_num) and state is True:
                self.fail('"%s" is running, but should not' % name)

    def assertLocalRegistryHasImage(self, image_name):
        self.assertIn(image_name, self.get_locally_pulled_docker_images(),
                      msg='Expected that "docker images" will contain image "%s"' % image_name)

    def assertLocalRegistryHasNoPulledImage(self, image_name):
        self.assertNotIn(image_name, self.get_locally_pulled_docker_images(),
                         msg='Expected that "docker images" will not contain image "%s"' % image_name)