from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.service import LogsTask
from rkd_harbor.service import ServiceDeclaration


class LogsTaskTest(BaseHarborTestClass):
    def test_will_print_logs_for_container(self):
        """Run command inside container, do not test output as it is passed-through directly to the console"""
        service = ServiceDeclaration('alpine_3', {})

        drv = self._get_prepared_compose_driver()
        drv.up(service, capture=True)

        out = self.execute_task(LogsTask(), args={
            'name': 'alpine_3',
            '--instance-num': 1,
            '--follow': False,
            '--buffered': True
        })

        self.assertIn('Hello', out)
