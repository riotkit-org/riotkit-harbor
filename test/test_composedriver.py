
from io import StringIO
from rkd.inputoutput import IO
from harbor.test import BaseHarborTestClass
from harbor.service import ServiceDeclaration


class ComposeDriverTest(BaseHarborTestClass):
    def test_get_compose_args_sets_basic_arguments_and_sees_yaml_configuration_files(self):
        drv = self._get_mocked_compose_driver()
        args = drv.get_compose_args()

        self.assertIn('--project-directory=', args, msg='Project directory should be set')
        self.assertIn('-p test', args, msg='Project name should be set')
        self.assertIn('-f docker-compose.yml', args, msg='Basic docker-compose.yml should be considered')
        self.assertIn('infrastructure.ssl.yml', args)
        self.assertIn('infrastructure.service-discovery.yml', args)
        self.assertIn('infrastructure.health.yml', args)

    def test_ps(self):
        """Simply check if docker-compose ps can be executed, if the standard switches are correct"""

        io_str = StringIO()
        io = IO()

        with io.capture_descriptors(target_file=None, stream=io_str, enable_standard_out=False):
            drv = self._get_mocked_compose_driver()
            drv.ps([])

        self.assertIn('Name', io_str.getvalue())
        self.assertIn('Ports', io_str.getvalue())

    def test_up(self):
        """Simply verify that the docker-compose up command is properly generated"""

        resulting_args = []

        # mock
        drv = self._get_mocked_compose_driver()
        drv.scope.sh = lambda *args, **kwargs: (resulting_args.append(args))

        # action
        drv.up(ServiceDeclaration('healthcheck', {}))

        args_as_str = ' '.join(resulting_args[0])

        self.assertIn('--scale healthcheck=1 healthcheck', args_as_str)
        self.assertIn('infrastructure.health.yml', args_as_str)
        self.assertIn('up -d', args_as_str)

    def test_up_invalid_parameters_for_recreation(self):
        drv = self._get_mocked_compose_driver()
        drv.scope.sh = lambda *args, **kwargs: ''

        # action
        self.assertRaises(Exception, lambda: drv.up(ServiceDeclaration('healthcheck', {}),
                                                    norecreate=True, force_recreate=True))

    def test_up_tolerates_extra_arguments(self):
        resulting_args = []
        drv = self._get_mocked_compose_driver()
        drv.scope.sh = lambda *args, **kwargs: (resulting_args.append(args))

        # action
        drv.up(ServiceDeclaration('healthcheck', {}), extra_args='--remove-orphans')
        args_as_str = ' '.join(resulting_args[0])

        self.assertIn('--remove-orphans', args_as_str)



