from harbor.test import BaseHarborTestClass
from harbor.tasks.maintenance import MaintenanceOnTask
from harbor.tasks.maintenance import MaintenanceOffTask


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
        self.execute_task(MaintenanceOnTask(), args={'--global': True, '--domain': ''})
        content = self.fetch_page_content('nginx-with-maintenance-mode.local')

        self.assertIn('503: Page maintenance', content)
        self.assertIn('HTTP/1.1 503', content)

        # 2) maintenance mode off
        self.execute_task(MaintenanceOffTask(), args={'--global': True, '--domain': ''})
        content = self.fetch_page_content('nginx-with-maintenance-mode.local')

        self.assertNotIn('503: Page maintenance', content)
        self.assertIn('HTTP/1.1 200', content)

    def test_global_maintenance_mode_not_affects_service_that_has_maintenance_off(self):
        """Verify that service that does not have `org.riotkit.useMaintenanceMode` label should not display maintenance
        page, even if global maintenance is on"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website', uses_service_discovery=True)

        # 1) maintenance on, then check - should not be under maintenance as service has maintenance off in definition
        self.execute_task(MaintenanceOnTask(), args={'--global': True, '--domain': ''})

        self.assertIn('HTTP/1.1 200', self.fetch_page_content('nginx.local'))
