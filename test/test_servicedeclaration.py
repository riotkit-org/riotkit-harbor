
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.service import ServiceDeclaration


class ServiceDeclarationTest(BaseHarborTestClass):
    def test_get_domains(self):
        """Test get_domains() with multiple domains"""

        example_service = {
            'image': 'nginx:1.19',
            'environment': {
                'VIRTUAL_HOST': 'abcf.net,www.abcf.net'
            }
        }

        service = ServiceDeclaration('anarchist_black_cross_federation', example_service)
        self.assertEqual(['abcf.net', 'www.abcf.net'], service.get_domains())

    def test_watchtower_getter_true(self):
        example_service = {
            'image': 'nginx:1.19',
            'labels': {
                'com.centurylinklabs.watchtower.enable': 'true'
            }
        }

        service = ServiceDeclaration('anarchist_black_cross_federation', example_service)
        self.assertTrue(service.is_using_watchtower())

    def test_watchtower_getter_default_value(self):
        example_service = {
            'image': 'nginx:1.19'
        }

        service = ServiceDeclaration('anarchist_black_cross_federation', example_service)
        self.assertFalse(service.is_using_watchtower())

    def test_watchtower_getter_false(self):
        example_service = {
            'image': 'nginx:1.19',
            'labels': {
                'com.centurylinklabs.watchtower.enable': 'false'
            }
        }

        service = ServiceDeclaration('anarchist_black_cross_federation', example_service)
        self.assertFalse(service.is_using_watchtower())

    def test_watchtower_getter_invalid_value_converts_to_false(self):
        example_service = {
            'image': 'nginx:1.19',
            'labels': {
                'com.centurylinklabs.watchtower.enable': 'INVALID VALUE!'
            }
        }

        service = ServiceDeclaration('anarchist_black_cross_federation', example_service)
        self.assertFalse(service.is_using_watchtower())

    def test_maintenance_mode_label_name(self):
        example_service = {
            'image': 'nginx:1.19',
            'labels': {
                'org.riotkit.useMaintenanceMode': 'True'
            }
        }

        service = ServiceDeclaration('anarchist_black_cross_federation', example_service)
        self.assertTrue(service.is_using_maintenance_mode())

    def test_get_ports(self):
        ports = [
            '80:80',
            '443:443',
            '8001:80001'
        ]

        example_service = {
            'image': 'nginx:1.19',
            'ports': ports
        }

        service = ServiceDeclaration('phillyabc', example_service)
        self.assertEqual(ports, service.get_ports())

    def test_get_desired_replicas_count_returns_one_as_default(self):
        example_service = {
            'image': 'nginx:1.19'
        }

        service = ServiceDeclaration('phillyabc', example_service)
        self.assertEqual(1, service.get_desired_replicas_count())

    def test_get_desired_replicas_count_returns_declared_count(self):
        example_service = {
            'image': 'nginx:1.19',
            'labels': {
                'org.riotkit.replicas': '5'
            }
        }

        service = ServiceDeclaration('phillyabc', example_service)
        self.assertEqual(5, service.get_desired_replicas_count())

    def test_get_update_strategy_returns_declared_default(self):
        example_service = {
            'image': 'nginx:1.19'
        }

        service = ServiceDeclaration('phillyabc', example_service)
        self.assertEqual('compose', service.get_update_strategy('compose'))

    def test_get_update_strategy_returns_declared_value_in_yaml(self):
        example_service = {
            'image': 'nginx:1.19',
            'labels': {
                'org.riotkit.updateStrategy': 'recreate'
            }
        }

        service = ServiceDeclaration('phillyabc', example_service)
        self.assertEqual('recreate', service.get_update_strategy('compose'))

    def test_get_image_returns_declared_image(self):
        example_service = {
            'image': 'nginx:1.19'
        }

        service = ServiceDeclaration('iwa_ait', example_service)
        self.assertEqual('nginx:1.19', service.get_image())

    def test_get_image_returns_local_build_string_when_no_image_specified(self):
        example_service = {}

        service = ServiceDeclaration('iwa_ait', example_service)
        self.assertEqual('_docker_build_local:latest', service.get_image())

    def test_get_declared_version_returns_build_version_when_no_image_declared(self):
        example_service = {}

        service = ServiceDeclaration('iwa_ait', example_service)
        self.assertEqual('latest (build)', service.get_declared_version())

    def test_get_declared_version_returns_latest_when_image_declared_without_version(self):
        example_service = {
            'image': 'quay.io/riotkit/wp-auto-update'
        }

        service = ServiceDeclaration('iwa_ait', example_service)
        self.assertEqual('latest', service.get_declared_version())
