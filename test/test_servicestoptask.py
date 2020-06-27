from harbor.test import BaseHarborTestClass
from harbor.tasks.service import ServiceStopTask
from harbor.service import ServiceDeclaration


class ServiceStopTaskTest(BaseHarborTestClass):
    def test_functional_service_is_stopped(self):
        """Start service, then try to bring down, leave the images"""
        service = ServiceDeclaration('alpine_3', {})

        drv = self._get_prepared_compose_driver()
        drv.up(service, capture=True)

        self.execute_task(ServiceStopTask(), args={
            'name': 'alpine_3',
            '--extra-args': ''
        })

        self.assertContainerIsNotRunning('alpine_3', drv)
