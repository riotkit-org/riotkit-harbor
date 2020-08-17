from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.service import ServiceSelector
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.inputoutput import IO


class ServiceSelectorTest(BaseHarborTestClass):
    def _provide_test_data(self) -> dict:
        return {
            'web_phillyabc': {
                'image': 'nginx:1.19',
                'labels': {
                    'org.riotkit.type': 'abc',
                    'org.riotkit.country': 'USA',
                    'org.riotkit.priority': 150
                }
            },
            'web_abc_international': {
                'image': 'nginx:1.19',
                'labels': {
                    'org.riotkit.type': 'abc',
                    'org.riotkit.priority': 100
                }
            },
            'web_iwa_ait': {
                'image': 'nginx:1.19',
                'labels': {
                    'org.riotkit.type': 'workers-union',
                    'org.riotkit.priority': 200
                }
            }
        }

    def test_find_matching_services_by_labels(self):
        """Test that services can be found by labels"""

        io = IO()
        selector = ServiceSelector(
            '"org.riotkit.type" in service["labels"] and service["labels"]["org.riotkit.type"] == "abc"', io
        )

        names = list(map(lambda service: service.get_name(),
                         selector.find_matching_services(self._provide_test_data())))

        self.assertEqual(['web_abc_international', 'web_phillyabc'], names)

    def test_find_matching_services_by_names(self):
        io = IO()
        selector = ServiceSelector('name.startswith("web")', io)

        names = list(map(lambda service: service.get_name(),
                         selector.find_matching_services(self._provide_test_data())))

        self.assertEqual(['web_abc_international', 'web_phillyabc', 'web_iwa_ait'], names)

    def test_find_matching_skips_services_on_syntax_error_but_raises_error_in_log(self):
        io = BufferedSystemIO()
        selector = ServiceSelector('service["labels"]["org.riotkit.country"] != ""', io)

        names = list(map(lambda service: service.get_name(),
                         selector.find_matching_services(self._provide_test_data())))

        self.assertEqual(['web_phillyabc'], names)
        self.assertIn("KeyError: 'org.riotkit.country'", io.get_value())
        self.assertIn("Exception raised, while attempting to evaluate --profile selector", io.get_value())

    def test_finding_matching_services_considers_priority_ascending(self):
        io = IO()
        selector = ServiceSelector('True', io)

        names = list(map(lambda service: service.get_name(),
                         selector.find_matching_services(self._provide_test_data())))

        with self.subTest('With test data from data provider'):
            self.assertEqual(['web_abc_international', 'web_phillyabc', 'web_iwa_ait'], names)

        with self.subTest('With modified priority orders'):
            test_data = self._provide_test_data()
            test_data['web_iwa_ait']['labels']['org.riotkit.priority'] = 50
            test_data['web_phillyabc']['labels']['org.riotkit.priority'] = -3

            names = list(map(lambda service: service.get_name(),
                             selector.find_matching_services(test_data)))

            self.assertEqual(['web_phillyabc', 'web_iwa_ait', 'web_abc_international'], names)

    def test_finding_matching_services_accepts_1000_as_default_priority(self):
        io = IO()
        selector = ServiceSelector('True', io)

        test_data = self._provide_test_data()
        test_data['web_iwa_ait']['labels']['org.riotkit.priority'] = 900
        del test_data['web_phillyabc']['labels']['org.riotkit.priority']
        test_data['web_abc_international']['labels']['org.riotkit.priority'] = 1200

        names = list(map(lambda service: service.get_name(), selector.find_matching_services(test_data)))

        self.assertEqual(['web_iwa_ait', 'web_phillyabc', 'web_abc_international'], names)
