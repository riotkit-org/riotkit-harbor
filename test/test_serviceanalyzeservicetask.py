from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.service import AnalyzeServiceTask
from rkd_harbor.service import ServiceDeclaration
from rkd_harbor.exception import ServiceNotFoundInYaml


class AnalyzeServiceTaskTest(BaseHarborTestClass):
    def test_report_shows_declared_and_actual_state_for_simple_service(self):
        service = ServiceDeclaration('alpine_3', {})

        drv = self._get_prepared_compose_driver()
        drv.up(service, capture=True)

        # assert it will not raise an error
        out = self.execute_task(AnalyzeServiceTask(), args={'name': 'alpine_3'})

        self.assertIn('Declared image:    alpine:3.11', out)
        self.assertIn('Update strategy:   compose', out)
        self.assertIn('Replicas:          1 of 1', out)
        self.assertIn('alpine:3.11', out)
        self.assertIn('env_simple_alpine_3_1', out)

    def test_shows_service_not_found_when_service_name_is_invalid(self):
        self.assertRaises(
            ServiceNotFoundInYaml,
            lambda: self.execute_task(AnalyzeServiceTask(), args={'name': 'invalid_name'})
        )
