import unittest
from harbor.service import ServiceLocator
from harbor.exception import ServiceNotFoundInYaml


class ServiceLocatorTest(unittest.TestCase):
    def test_get_by_name_finds_service_and_returns_as_object(self):
        locator = ServiceLocator({
            'web_iwa_ait': {},
            'web_priamaakcia': {}
        })

        service = locator.get_by_name('web_priamaakcia')
        self.assertEqual('web_priamaakcia', service.get_name())

    def test_get_by_name_does_not_find_service_when_its_name_is_not_properly_specified(self):
        locator = ServiceLocator({
            'web_iwa_ait': {},
            'web_priamaakcia': {}
        })

        self.assertRaises(ServiceNotFoundInYaml, lambda: locator.get_by_name('non_existing'))
