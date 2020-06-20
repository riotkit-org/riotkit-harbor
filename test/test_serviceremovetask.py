from harbor.test import BaseHarborTestClass
from harbor.tasks.service import ServiceRemoveTask
from harbor.service import ServiceDeclaration


class ServiceRemoveTaskTest(BaseHarborTestClass):
    def test_functional_service_is_stopped_and_removed(self):
        """Test that service is stopped and removed, together with two instances

        1. Creates one instance + one replica
        2. Removes service
        3. Expects that two instances were removed
        """

        service = ServiceDeclaration('website', {})

        drv = self._get_prepared_compose_driver()
        drv.rm(service, capture=True)
        drv.up(service, capture=True)
        drv.scale_one_up(service)

        out = self.execute_task(ServiceRemoveTask(), debug=False, args={
            'name': 'website',
            '--with-image': False,
            '--extra-args': ''
        })

        containers = self.get_containers_state(drv)

        for container_name, state in containers.items():
            if container_name.startswith('test_website_'):
                self.fail('Found %s container, which should be removed by calling :harbor:service:rm')

        self.assertIn('Removing test_website_1', out)
        self.assertIn('Removing test_website_2', out)

    def test_functional_service_is_removed_together_with_image(self):
        service = ServiceDeclaration('alpine_3', {})

        drv = self._get_prepared_compose_driver()
        drv.up(service, capture=True)

        self.execute_task(ServiceRemoveTask(), debug=False, args={
            'name': 'alpine_3',
            '--with-image': True,
            '--extra-args': ''
        })

        self.assertLocalRegistryHasNoPulledImage('alpine:3.11')