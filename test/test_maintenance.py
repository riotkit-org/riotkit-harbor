from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.maintenance import MaintenanceOnTask
from rkd_harbor.tasks.maintenance import MaintenanceOffTask


class TestMaintenanceModeFeature(BaseHarborTestClass):
    """Functional tests for the maintenance feature

    Includes coverage of:
        - Tasks
        - NGINX template
    """

    def test_functional_global_maintenance_will_be_on_then_off(self):
        """Simply test global maintenance mode switch for services that have label
         `org.riotkit.useMaintenanceMode: true`"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website_with_maintenance', uses_service_discovery=True)

        # 1) maintenance on
        with self.subTest('Maintenance mode on'):
            self.execute_task(MaintenanceOnTask(), args={'--global': True, '--domain': '', '--service': ''})
            content = self.fetch_page_content('nginx-with-maintenance-mode.local')

            self.assertIn('503: Page maintenance', content)
            self.assertIn('HTTP/1.1 503', content)

        # 2) maintenance mode off
        with self.subTest('Maintenance mode off'):
            self.execute_task(MaintenanceOffTask(), args={'--global': True, '--domain': '', '--service': ''})
            content = self.fetch_page_content('nginx-with-maintenance-mode.local')

            self.assertNotIn('503: Page maintenance', content)
            self.assertIn('HTTP/1.1 200', content)

    def test_functional_global_maintenance_mode_not_affects_service_that_has_maintenance_off(self):
        """Verify that service that does not have `org.riotkit.useMaintenanceMode` label should not display maintenance
        page, even if global maintenance is on"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website', uses_service_discovery=True)

        # 1) maintenance on, then check - should not be under maintenance as service has maintenance off in definition
        self.execute_task(MaintenanceOnTask(), args={'--global': True, '--domain': '', '--service': ''})

        self.assertIn('HTTP/1.1 200', self.fetch_page_content('nginx.local'))

    def test_functional_maintenance_mode_for_service(self):
        """Verify that if we want to put a SERVICE in maintenance mode, then all DOMAINS of that SERVICE will be
        in maintenance"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website_with_multiple_domains', uses_service_discovery=True)

        # 1) maintenance on
        with self.subTest('Turning maintenance on'):
            self.execute_task(MaintenanceOnTask(), args={
                '--global': False, '--domain': '', '--service': 'website_with_multiple_domains'
            })

            self.assertIn('HTTP/1.1 503', self.fetch_page_content('web1.local'))
            self.assertIn('HTTP/1.1 503', self.fetch_page_content('web2.local'))
            self.assertIn('HTTP/1.1 503', self.fetch_page_content('web3.local'))

        # 2) maintenance off
        with self.subTest('Turning off the maintenance'):
            self.execute_task(MaintenanceOffTask(), args={
                '--global': False, '--domain': '', '--service': 'website_with_multiple_domains'
            })

            self.assertIn('HTTP/1.1 200', self.fetch_page_content('web1.local'))
            self.assertIn('HTTP/1.1 200', self.fetch_page_content('web2.local'))
            self.assertIn('HTTP/1.1 200', self.fetch_page_content('web3.local'))

    def test_functional_maintenance_mode_for_single_domain_under_service_that_has_multiple_domains(self):
        """Test that we can set a maintenance for domain web1.local, while web2.local stays normal
        WHERE both domains are under SAME service"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website_with_multiple_domains', uses_service_discovery=True)

        # 1) maintenance on
        self.execute_task(MaintenanceOnTask(), args={
            '--global': False, '--domain': 'web1.local', '--service': ''
        })

        self.assertIn('HTTP/1.1 503', self.fetch_page_content('web1.local'))
        self.assertIn('HTTP/1.1 200', self.fetch_page_content('web2.local'))

    def test_validation_of_domain_parameter(self):
        """Try to set a maintenance mode for domain not defined in YAML"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website_with_multiple_domains', uses_service_discovery=True)

        out = self.execute_task(MaintenanceOnTask(), args={
            '--global': False, '--domain': 'invalid_domain.local', '--service': ''
        })

        self.assertIn('Domain is not valid', out)

    def test_validation_of_service_parameter(self):
        """Try to set a maintenance mode for service that is not defined in YAML"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website_with_multiple_domains', uses_service_discovery=True)

        out = self.execute_task(MaintenanceOnTask(), args={
            '--global': False, '--domain': '', '--service': 'non_existing_service'
        })

        self.assertIn('Service "non_existing_service" was not defined', out)
