from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.configsmanagement import EnableConfigTask
from rkd_harbor.tasks.configsmanagement import DisableConfigTask
from rkd_harbor.tasks.configsmanagement import ListConfigsTask


class ConfigsManagementTest(BaseHarborTestClass):

    def test_functional_configs_can_be_listed_enabled_and_disabled(self):
        """Test listing, enabling and disabling
        """

        self.assertIn('conf/infrastructure.service-discovery.yml  Yes', self.execute_task(ListConfigsTask(), args={}))

        with self.subTest('Disable service discovery'):
            disable_task = DisableConfigTask()
            disable_task.git_commands_suffix = '|| true'
            disable_task.git_mv_command = 'mv'

            self.execute_task(disable_task, args={'--name': 'conf/infrastructure.service-discovery.yml'})
            self.assertRegex(self.execute_task(ListConfigsTask(), args={}),
                             'conf/infrastructure.service-discovery.yml.*No')

        with self.subTest('Enable service discovery'):
            enable_task = EnableConfigTask()
            enable_task.git_commands_suffix = '|| true'
            enable_task.git_mv_command = 'mv'

            self.execute_task(enable_task, args={'--name': 'conf/infrastructure.service-discovery.yml'})
            self.assertRegex(self.execute_task(ListConfigsTask(), args={}),
                             'conf/infrastructure.service-discovery.yml.*Yes')
