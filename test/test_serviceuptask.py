from harbor.test import BaseHarborTestClass
from harbor.tasks.service import ServiceUpTask
from harbor.service import ServiceDeclaration


class ServiceUpTaskTest(BaseHarborTestClass):
    def test_functional_service_is_getting_recreated(self):
        """Test that service is recreated"""

        drv = self._get_prepared_compose_driver()
        drv.stop('website', capture=True)

        for i in range(1, 2):
            out = self.prepare_task(ServiceUpTask(), args={
                'name': 'website',
                '--strategy': 'recreate',
                '--remove-previous-images': False,
                '--extra-args': ''
            })

            self.assertIn('Recreating test_website_1', out)

    def test_functional_service_is_rolling_updated(self):
        """Test that service rolling update is performed"""

        drv = self._get_prepared_compose_driver()
        drv.rm(ServiceDeclaration('website', {}), capture=True)
        drv.up(ServiceDeclaration('website', {}), capture=True)

        out = self.prepare_task(ServiceUpTask(), debug=False, args={
            'name': 'website',
            '--strategy': 'rolling',
            '--remove-previous-images': False,
            '--extra-args': ''
        })

        self.assertIn('Stopping test_gateway_proxy_gen_1', out,
                      msg='Expected the rolling strategy will stop proxy_gen')
        self.assertIn('Starting test_gateway_proxy_gen_1', out,
                      msg='Expected the rolling strategy will start proxy_gen')

        running_containers = self.get_containers_state(drv)

        self.assertIn('test_website_2', running_containers,
                      msg='Expected that a new instance would be in place of old one')
        self.assertNotIn('test_website_1', running_containers,
                         msg='Expected that the old container will be turned off')

    def test_functional_compose_method_is_executed(self):
        """Test that the service is not force-recreated by 'compose' method"""

        drv = self._get_prepared_compose_driver()
        drv.rm(ServiceDeclaration('website', {}), capture=True)
        drv.up(ServiceDeclaration('website', {}), capture=True)

        out = self.prepare_task(ServiceUpTask(), debug=False, args={
            'name': 'website',
            '--strategy': 'compose',
            '--remove-previous-images': False,
            '--extra-args': '',
            '--dont-recreate': False
        })

        self.assertIn('test_website_1 is up-to-date', out)

    def test_strategy_is_automatically_selected_from_service_definition(self):
        """Strategy if not defined in YAML will be fallback to default: 'compose'"""

        drv = self._get_prepared_compose_driver()
        drv.rm(ServiceDeclaration('website', {}), capture=True)

        out = self.prepare_task(ServiceUpTask(), debug=False, args={
            'name': 'website',
            '--strategy': 'auto',
            '--remove-previous-images': False,
            '--extra-args': '',
            '--dont-recreate': False
        })

        self.assertIn('Performing "compose"', out)

    def test_invalid_strategy_raises_error(self):
        """Tests that enum is validated"""

        drv = self._get_prepared_compose_driver()
        drv.rm(ServiceDeclaration('website', {}), capture=True)

        out = self.prepare_task(ServiceUpTask(), debug=False, args={
            'name': 'website',
            '--strategy': 'invalid-strategy-name',
            '--remove-previous-images': False,
            '--extra-args': '',
            '--dont-recreate': False
        })

        self.assertIn('Invalid strategy selected: invalid-strategy-name', out)
