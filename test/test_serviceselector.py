from harbor.test import BaseHarborTestClass
from harbor.service import ServiceSelector
from rkd.inputoutput import BufferedSystemIO


class ServiceSelectorTest(BaseHarborTestClass):
    def _provide_test_data(self) -> dict:
        return {
            'web_phillyabc': {
                'image': 'nginx:1.19',
                'labels': {
                    'org.riotkit.type': 'abc',
                    'org.riotkit.country': 'USA'
                }
            },
            'web_abc_international': {
                'image': 'nginx:1.19',
                'labels': {
                    'org.riotkit.type': 'abc'
                }
            },
            'web_iwa_ait': {
                'image': 'nginx:1.19',
                'labels': {
                    'org.riotkit.type': 'workers-union'
                }
            }
        }

    def test_find_matching_services_by_labels(self):
        """Test that services can be found by labels"""

        io = BufferedSystemIO()
        selector = ServiceSelector(
            '"org.riotkit.type" in service["labels"] and service["labels"]["org.riotkit.type"] == "abc"', io
        )

        names = list(map(lambda service: service.get_name(),
                         selector.find_matching_services(self._provide_test_data())))

        self.assertEqual(['web_phillyabc', 'web_abc_international'], names)

    def test_find_matching_services_by_names(self):
        io = BufferedSystemIO()
        selector = ServiceSelector('name.startswith("web")', io)

        names = list(map(lambda service: service.get_name(),
                         selector.find_matching_services(self._provide_test_data())))

        self.assertEqual(['web_phillyabc', 'web_abc_international', 'web_iwa_ait'], names)

    def test_find_matching_skips_services_on_syntax_error_but_raises_error_in_log(self):
        io = BufferedSystemIO()
        selector = ServiceSelector('service["labels"]["org.riotkit.country"] != ""', io)

        names = list(map(lambda service: service.get_name(),
                         selector.find_matching_services(self._provide_test_data())))

        self.assertEqual(['web_phillyabc'], names)
        self.assertIn("KeyError: 'org.riotkit.country'", io.get_value())
        self.assertIn("Exception raised, while attempting to evaluate --profile selector", io.get_value())
