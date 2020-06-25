from harbor.test import BaseHarborTestClass
from harbor.tasks.configsmanagement import EnableConfigTask
from harbor.tasks.configsmanagement import DisableConfigTask
from harbor.tasks.configsmanagement import ListConfigsTask


class ConfigsManagementTest(BaseHarborTestClass):

    def test_functional_configs_can_be_listed_enabled_and_disabled(self):
        """Test listing, enabling and disabling
        """

        self.assertIn('conf/infrastructure.service-discovery.yml  Yes', self.execute_task(ListConfigsTask(), args={}))

        with self.subTest('Disable service discovery'):
            self.execute_task(DisableConfigTask(), args={'--name': 'conf/infrastructure.service-discovery.yml'})
            self.assertIn('conf/infrastructure.service-discovery.yml  No',
                          self.execute_task(ListConfigsTask(), args={}))

        with self.subTest('Enable service discovery'):
            self.execute_task(EnableConfigTask(), args={'--name': 'conf/infrastructure.service-discovery.yml'})
            self.assertIn('conf/infrastructure.service-discovery.yml  Yes',
                          self.execute_task(ListConfigsTask(), args={}))
