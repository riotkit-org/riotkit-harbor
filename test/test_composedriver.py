
import requests
from time import time
from io import StringIO
from rkd.api.inputoutput import IO
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.service import ServiceDeclaration
from rkd_harbor.exception import ServiceNotCreatedException
from rkd_harbor.exception import ServiceNotReadyException


class ComposeDriverTest(BaseHarborTestClass):
    def test_get_compose_args_sets_basic_arguments_and_sees_yaml_configuration_files(self):
        drv = self._get_prepared_compose_driver()
        args = drv.get_compose_args()

        self.assertIn('--project-directory=', args, msg='Project directory should be set')
        self.assertIn('-p env_simple', args, msg='Project name should be set')
        self.assertIn('-f docker-compose.yml', args, msg='Basic docker-compose.yml should be considered')
        self.assertIn('infrastructure.ssl.yml', args)
        self.assertIn('infrastructure.service-discovery.yml', args)
        self.assertIn('infrastructure.health.yml', args)

    def test_ps(self):
        """Simply check if docker-compose ps can be executed, if the standard switches are correct"""

        io_str = StringIO()
        io = IO()

        with io.capture_descriptors(stream=io_str, enable_standard_out=False):
            drv = self._get_prepared_compose_driver()
            drv.ps([])

        self.assertIn('Name', io_str.getvalue())
        self.assertIn('Ports', io_str.getvalue())

    def test_up(self):
        """Simply verify that the docker-compose up command is properly generated"""

        resulting_args = []

        # mock
        drv = self._get_prepared_compose_driver()
        drv.scope.sh = lambda *args, **kwargs: (resulting_args.append(args))

        # action
        drv.up(ServiceDeclaration('healthcheck', {}))

        args_as_str = ' '.join(resulting_args[0])

        self.assertIn('--scale healthcheck=1 healthcheck', args_as_str)
        self.assertIn('infrastructure.health.yml', args_as_str)
        self.assertIn('up -d', args_as_str)

    def test_up_invalid_parameters_for_recreation(self):
        """Unit test: Checks if exception is raised when logic error happens"""

        drv = self._get_prepared_compose_driver()
        drv.scope.sh = lambda *args, **kwargs: ''

        # action
        self.assertRaises(Exception, lambda: drv.up(ServiceDeclaration('healthcheck', {}),
                                                    norecreate=True, force_recreate=True))

    def test_up_tolerates_extra_arguments(self):
        """Unit tests: Checks if extra arguments are allowed to be passed"""

        resulting_args = []
        drv = self._get_prepared_compose_driver()
        drv.scope.sh = lambda *args, **kwargs: (resulting_args.append(args))

        # action
        drv.up(ServiceDeclaration('healthcheck', {}), extra_args='--remove-orphans')
        args_as_str = ' '.join(resulting_args[0])

        self.assertIn('--remove-orphans', args_as_str)

    def test_functional_up_and_down(self):
        """Functional test to start, stop, restart, remove container
           Checks basic compatibility with docker-compose interface
        """

        drv = self._get_prepared_compose_driver()

        # 1) Start
        drv.up(ServiceDeclaration('gateway', {}))
        self.assertTrue(self.get_containers_state(drv)['env_simple_gateway_1'])

        # 2) Restart
        drv.restart('gateway')
        self.assertTrue(self.get_containers_state(drv)['env_simple_gateway_1'])

        # 3) Stop
        drv.stop('gateway')
        self.assertFalse(self.get_containers_state(drv)['env_simple_gateway_1'])

        # 4) Remove
        drv.rm(ServiceDeclaration('gateway', {}))
        self.assertNotIn('env_simple_gateway_1', self.get_containers_state(drv))

    def test_get_last_container_name_for_service(self):
        drv = self._get_prepared_compose_driver()

        # make sure it is clean up
        drv.rm(ServiceDeclaration('gateway', {}), capture=True)  # there may be more instances, so remove them
        drv.up(ServiceDeclaration('gateway', {}), capture=True)  # bring one instance

        self.assertEqual('env_simple_gateway_1', drv.get_last_container_name_for_service('gateway'))

    def test_find_container_name_case_service_not_created_raises_exception(self):
        drv = self._get_prepared_compose_driver()

        self.assertRaises(
            ServiceNotCreatedException,
            lambda: drv.find_container_name(ServiceDeclaration('not_existing', {}))
        )

    def test_find_container_name_finds_first_instance_when_no_instance_specified(self):
        drv = self.prepare_example_service('gateway')

        instance_name = drv.find_container_name(ServiceDeclaration('gateway', {}))
        self.assertEqual('env_simple_gateway_1', instance_name)

    def test_find_container_name_finds_first_instance_by_specyfing_instance_num(self):
        drv = self.prepare_example_service('gateway')

        self.assertEqual(
            'env_simple_gateway_1',
            drv.find_container_name(ServiceDeclaration('gateway', {}), instance_num=1)
        )

    def test_find_container_name_does_not_find_instance_when_there_is_not_enough_replicas(self):
        drv = self.prepare_example_service('gateway')

        # for single works
        self.assertEqual('env_simple_gateway_1', drv.find_container_name(ServiceDeclaration('gateway', {}), instance_num=1))

        self.assertRaises(
            ServiceNotCreatedException,
            lambda: drv.find_container_name(ServiceDeclaration('gateway', {}), instance_num=50)
        )

    def test_wait_for_log_message_finds_searched_phrase(self):
        drv = self.prepare_example_service('gateway')

        requests.get('http://localhost:8000')
        self.assertTrue(
            drv.wait_for_log_message('GET / HTTP/1.1', ServiceDeclaration('gateway', {}), timeout=5)
        )

    def test_wait_for_log_hits_timeout(self):
        drv = self.prepare_example_service('gateway')

        start_time = time()

        self.assertRaises(
            ServiceNotReadyException,
            lambda: drv.wait_for_log_message(
                'Some message that should be there',
                ServiceDeclaration('gateway', {}),
                timeout=2
            )
        )

        self.assertGreaterEqual(time() - start_time, 2, msg='Expected at least two seconds waiting')

    def test_scale_one_up_then_scale_down_to_desired_state(self):
        """Functional test: Scale one up, then down to declared state

        Covers:
            scale_one_up()
            scale_to_desired_state()
        """

        drv = self.prepare_example_service('website')
        drv.scale_one_up(ServiceDeclaration('website', {}))

        running_containers = self.get_containers_state(drv)
        self.assertIn('env_simple_website_1', running_containers)
        self.assertIn('env_simple_website_2', running_containers)

    def test_find_all_container_names_for_service_finds_containers(self):
        drv = self.prepare_example_service('website')

        self.assertEqual(['env_simple_website_1'],
                         drv.find_all_container_names_for_service(ServiceDeclaration('website', {})))

        drv.scale_one_up(ServiceDeclaration('website', {}))
        containers = drv.find_all_container_names_for_service(ServiceDeclaration('website', {}))

        self.assertIn('env_simple_website_1', containers)
        self.assertIn('env_simple_website_2', containers)

    def test_find_all_container_names_for_service_raises_exception_on_invalid_service_name(self):
        drv = self._get_prepared_compose_driver()

        self.assertRaises(
            ServiceNotCreatedException,
            lambda: drv.find_all_container_names_for_service(ServiceDeclaration('not_existing', {}))
        )

    def test_get_created_containers_is_returning_containers_in_proper_order(self):
        """Test that get_created_containers() is preserving order"""

        drv = self._get_prepared_compose_driver()

        # create three instances of a service
        drv.up(ServiceDeclaration('website', {}))
        drv.scale_one_up(ServiceDeclaration('website', {}))

        containers = drv.get_created_containers(only_running=False)
        self.assertEqual([1, 2], list(containers['website'].keys()))

    def test_get_created_containers_is_showing_only_running_containers(self):
        """Test that 'website' service will be created, but will have no active containers"""

        drv = self._get_prepared_compose_driver()

        # create three instances of a service
        drv.up(ServiceDeclaration('website', {}))
        drv.stop('website')

        containers = drv.get_created_containers(only_running=True)
        self.assertEqual([], list(containers['website']))
