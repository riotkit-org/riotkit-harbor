from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.service import ExecTask
from rkd_harbor.service import ServiceDeclaration


class ServiceStopTaskTest(BaseHarborTestClass):
    def test_exec_can_pass_simple_commandline(self):
        """Run command inside container, do not test output as it is passed-through directly to the console"""
        service = ServiceDeclaration('alpine_3', {})

        drv = self._get_prepared_compose_driver()
        drv.up(service, capture=True)

        # assert it will not raise an error
        self.execute_task(ExecTask(), args={
            'name': 'alpine_3',
            '--extra-args': '',
            '--command': 'exit 0',
            '--shell': '/bin/sh',
            '--instance-num': None,

            # in tests its reversed
            '--no-tty': False,
            '--no-interactive': True
        })
