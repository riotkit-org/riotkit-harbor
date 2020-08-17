from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.service import WaitForServiceTask
from rkd_harbor.service import ServiceDeclaration
from rkd_harbor.exception import ServiceNotFoundInYaml


class WaitForServiceTaskTest(BaseHarborTestClass):
    def test_functional_waits_for_service_without_healthcheck(self):
        """Expect that the task will wait for container to be up, but will not check its health check if healthcheck
        was not defined"""

        drv = self._get_prepared_compose_driver()
        drv.up(ServiceDeclaration('alpine_3', {}), capture=True)
        drv.stop('alpine_3', capture=True)

        out = self.execute_task(WaitForServiceTask(), args={
            'name': 'alpine_3',
            '--timeout': 1,
            '--instance': 1
        })

        self.assertIn('Instance has no healthcheck defined!', out)

    def test_functional_timeout_is_raised(self):
        """Expects that the timeout will be raised, as it is very low in test"""

        drv = self._get_prepared_compose_driver()
        drv.up(ServiceDeclaration('alpine_3_health_check', {}), capture=True)

        out = self.execute_task(WaitForServiceTask(), args={
            'name': 'alpine_3_health_check',
            '--timeout': 0,
            '--instance': 1
        })

        self.assertIn('Timeout of 0s reached.', out)

    def test_functional_container_is_healthy_after_few_seconds_using_health_check_invoking_while_container_is_starting(self):
        """Expects that the container will become health within few seconds,
        even if docker daemon is showing 'starting'"""

        drv = self._get_prepared_compose_driver()
        drv.rm(ServiceDeclaration('alpine_3_health_check', {}), capture=True)
        drv.up(ServiceDeclaration('alpine_3_health_check', {}), capture=True)

        out = self.execute_task(WaitForServiceTask(), args={
            'name': 'alpine_3_health_check',
            '--timeout': 10,
            '--instance': 1
        })

        self.assertIn('Service healthy after', out)

    def test_will_not_wait_for_invalid_service(self):
        """Expects that the container will become health within few seconds,
        even if docker daemon is showing 'starting'"""

        self.assertRaises(ServiceNotFoundInYaml, lambda: self.execute_task(WaitForServiceTask(), args={
                                'name': 'not_existing_service',
                                '--timeout': 10,
                                '--instance': 1
                            })
                          )


