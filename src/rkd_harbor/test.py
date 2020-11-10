import os
import subprocess
import time
import yaml
from dotenv import dotenv_values
from typing import Dict
from copy import deepcopy
from argparse import ArgumentParser
from rkd.api.contract import ExecutionContext
from rkd.api.inputoutput import BufferedSystemIO
from rkd.api.syntax import TaskDeclaration
from rkd.api.testing import FunctionalTestingCase
from .tasks.base import HarborBaseTask
from .service import ServiceDeclaration
from .driver import ComposeDriver
from .cached_loader import CachedLoader

HARBOR_MODULE_PATH = os.path.dirname(os.path.realpath(__file__))
ENV_SIMPLE_PATH = os.path.dirname(os.path.realpath(__file__)) + '/../../test/testdata/env_simple'
CURRENT_TEST_ENV_PATH = os.path.dirname(os.path.realpath(__file__)) + '/../../test/testdata/current_test_env'
TEST_PROJECT_NAME = 'env_simple'


class TestTask(HarborBaseTask):
    is_dev_env = True

    def get_name(self) -> str:
        return ':test'

    def get_group_name(self) -> str:
        return ''

    def execute(self, context: ExecutionContext) -> bool:
        return True

    def run(self, context: ExecutionContext) -> bool:
        return True

    def configure_argparse(self, parser: ArgumentParser):
        pass


class BaseHarborTestClass(FunctionalTestingCase):
    def setUp(self) -> None:
        super().setUp()

        print('')
        print('==================================================================================================' +
              '=====================================')
        print('Test name: ' + self.__class__.__name__ + ' :: ' + self._testMethodName)
        print('----------')
        print('')

        CachedLoader.clear()   # avoid keeping the state between tests

        os.chdir(HARBOR_MODULE_PATH)
        self.recreate_structure()
        self.setup_environment()
        self.remove_all_containers()

    @classmethod
    def mock_compose(cls, content: dict):
        content['version'] = '3.4'

        with open(CURRENT_TEST_ENV_PATH + '/apps/conf/mocked.yaml', 'wb') as f:
            f.write(yaml.dump(content).encode('utf-8'))

    @classmethod
    def recreate_structure(cls):
        """Within each class recreate the project structure, as it could be changed by tests itself"""

        subprocess.check_call(['rm', '-rf', CURRENT_TEST_ENV_PATH])
        subprocess.check_call(['cp', '-pr', ENV_SIMPLE_PATH, CURRENT_TEST_ENV_PATH])

        # copy from base structure - as we test eg. things like default configurations, NGINX template
        for directory in ['containers', 'data', 'hooks.d', 'apps/www-data']:
            subprocess.check_call('rm -rf %s/%s' % (ENV_SIMPLE_PATH, directory), shell=True)
            subprocess.check_call('cp -pr %s/project/%s %s/%s' % (
                HARBOR_MODULE_PATH, directory, CURRENT_TEST_ENV_PATH, directory
            ), shell=True)

        cls.mock_compose({'services': {}})

    @classmethod
    def get_test_env_subdirectory(cls, subdir_name: str):
        directory = CURRENT_TEST_ENV_PATH + '/' + subdir_name

        if not os.path.isdir(directory):
            subprocess.check_call(['mkdir', '-p', directory])

        return os.path.realpath(directory)

    @classmethod
    def remove_all_containers(cls):
        try:
            subprocess.check_output("docker rm -f -v $(docker ps -a --format '{{ .Names }}' | grep " + TEST_PROJECT_NAME + ")",
                                    shell=True, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            # no containers found - it's OK
            if "requires at least 1 argument" in str(e.output):
                return

            raise e

    @classmethod
    def setup_environment(cls):
        os.environ.update(dotenv_values(CURRENT_TEST_ENV_PATH + '/.env'))
        os.environ['APPS_PATH'] = CURRENT_TEST_ENV_PATH + '/apps'
        os.environ['RKD_PATH'] = cls.get_test_env_subdirectory('') + ':' + HARBOR_MODULE_PATH + '/internal'

        os.chdir(CURRENT_TEST_ENV_PATH)

    def _get_prepared_compose_driver(self, args: dict = {}, env: dict = {}) -> ComposeDriver:
        merged_env = deepcopy(os.environ)
        merged_env.update(env)

        task = self.satisfy_task_dependencies(TestTask(), BufferedSystemIO())
        declaration = TaskDeclaration(task)
        ctx = ExecutionContext(declaration, args=args, env=merged_env)

        return ComposeDriver(task, ctx, TEST_PROJECT_NAME)

    @staticmethod
    def prepare_service_discovery(driver: ComposeDriver):
        driver.up(ServiceDeclaration('gateway', {}), capture=True, force_recreate=True)
        driver.up(ServiceDeclaration('gateway_proxy_gen', {}), capture=True, force_recreate=True)
        driver.up(ServiceDeclaration('website', {}), capture=True)

    def prepare_example_service(self, name: str, uses_service_discovery: bool = False) -> ComposeDriver:
        drv = self._get_prepared_compose_driver()

        # prepare
        drv.rm(ServiceDeclaration(name, {}))
        drv.up(ServiceDeclaration(name, {}))

        if uses_service_discovery:
            # give service discovery some time
            # @todo: This can be improved possibly
            time.sleep(10)

        return drv

    def get_containers_state(self, driver: ComposeDriver) -> Dict[str, bool]:
        running_rows = driver.scope.sh('docker ps -a --format "{{ .Names }}|{{ .Status }}"', capture=True).split("\n")
        containers = {}

        for container_row in running_rows:
            try:
                name, status = container_row.split('|')
            except ValueError:
                continue

            if name.startswith(driver.project_name + '_'):
                containers[name] = 'Up' in status

        return containers

    def get_locally_pulled_docker_images(self) -> list:
        images = subprocess.check_output(['docker', 'images', '--format', '{{ .Repository }}:{{ .Tag }}'])\
            .decode('utf-8')\
            .split("\n")

        return images

    def exec_in_container(self, container_name: str, cmd: list) -> str:
        return subprocess.check_output(
            ['docker', 'exec', '-i', container_name] + cmd,
            stderr=subprocess.STDOUT
        ).decode('utf-8')

    def fetch_page_content(self, host: str):
        return self.exec_in_container(TEST_PROJECT_NAME + '_gateway_1', ['curl', '-s', '-vv', '--header',
                                                                         'Host: %s' % host, 'http://127.0.0.1'])

    def prepare_valid_deployment_yml(self):
        """Internal: Prepares a valid deployment.yml and already synchronized files structure, downloaded role"""

        with open(self.get_test_env_subdirectory('') + '/deployment.yml', 'w') as f:
            f.write('''deploy_user: vagrant
deploy_group: vagrant
remote_dir: /project
git_url: https://github.com/riotkit-org/empty
git_secret_url: https://github.com/riotkit-org/empty
configure_sudoers: no

nodes:
    production:
        # example configuration for testing environment based on Vagrant
        # to run the environment type: harbor :deployment:vagrant -c "up --provision"
        - host: 127.0.0.1
          port: 2222
          user: docker
          password: docker
''')

    def prepare_valid_deployment_yml_encrypted_with_password_test(self):
        """Internal: Prepares a valid deployment.yml, same as prepare_valid_deployment_yml() but encrypted with vault

        Password is: test
        """

        with open(self.get_test_env_subdirectory('') + '/deployment.yml', 'w') as f:
            f.write('''$ANSIBLE_VAULT;1.1;AES256
39663866386139633138326634303139323266323236613732326366376531623239333465613438
3831373936306261316663383130316130643434343266630a643363303630626161333437313163
33313266316361653939373334323561326439323732363931303330313364363637303665303065
6262636637636633340a316436366131636363643233653163343733386632383439646336336137
33393138336364626265633438373661383835373463656465646361313832653337306332663434
35333034343865653361353261306464383336326130626266346336353738313066353639663539
61303031383738613333363034383166363332306665303533306465336335383234376230366339
38383134333431303333356666333535316465613865616539356538623734363434383164623865
32376438323665336564663135323163633561313730383930373339666166353761653038393930
35613233616562376337613232613861653562636132316238343434326530393338636465323031
35646532393135623561366634366561353132626532323732653534396435653833613934313030
30383763303161623733356134303863396365326330306437656465333761633833323662663564
63336435386566356232653263656162396132643264613261633235313237386465333362373537
30623131653235616366393337316638613863396364323831393430643363346366303631376632
39303361336365336266386639343432396533343639373832386533346263663965643765363738
39316235336539653962663232386436323034613464393732373432393033656366393139613834
35623230323733623235313935393838383161383866363165346235346230623932656631643838
64616661633039323166303934326163366532633732396162653236353965333135623264633939
62616532656637663061623230333838333432323134323761393334656339373338636530643237
34343634303138383138376364303236343532396638346562323764343665633165333433363937
34373665323733653435663938343665326162363862396139366438623062613963633565393166
39316431373561653163363035383365393430373833396631303563343030303836643533333631
61323534343963336265373465343438373536346235333633623130353536376461353233363636
35376361313332393236363235646431376630366164613764363332663639376234383963653231
33616236353832666262373037656332333637663962643462333662386363616266636635616266
39356436633130623561373061346338663062633636376438653764313539623831313433613764
64356532333466346264626362336632653335363461386436313536353334393865373565303839
34313962656236383736
''')

    def prepare_valid_deployment_yml_with_private_key(self):
        """
        Internal: Prepares a valid deployment.yml that has private key
        """

        with open(self.get_test_env_subdirectory('') + '/deployment.yml', 'w') as f:
            f.write('''deploy_user: vagrant
deploy_group: vagrant
remote_dir: /project
git_url: https://github.com/riotkit-org/empty
git_secret_url: https://github.com/riotkit-org/empty
configure_sudoers: no

nodes:
    production:
        # example configuration for testing environment based on Vagrant
        # to run the environment type: harbor :deployment:vagrant -c "up --provision"
        - host: 127.0.0.1
          port: 2222
          user: docker
          password: docker
          sudo_password: "sudo-docker"
          
          private_key: |
              -----BEGIN OPENSSH PRIVATE KEY-----
              b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAaAAAABNlY2RzYS
              1zaGEyLW5pc3RwMjU2AAAACG5pc3RwMjU2AAAAQQQO77Y+XtGXYUUb5VUVCy6EBX41aaTc
              hB4Qhz1dkpFDqZ86k+/acKOLyHxvN48nemEw0d7mhcQqq0yo2T1tqtfGAAAAsIQxjkeEMY
              5HAAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBA7vtj5e0ZdhRRvl
              VRULLoQFfjVppNyEHhCHPV2SkUOpnzqT79pwo4vIfG83jyd6YTDR3uaFxCqrTKjZPW2q18
              YAAAAhANr1bWf4C6H8pZTxudh3Y1W2esX7ea1BFd8K8wdF43h3AAAAFGtyenlzaWVrQHJp
              b3RraXQtb3BzAQID
              -----END OPENSSH PRIVATE KEY-----
    ''')

    def assertContainerIsNotRunning(self, service_name: str, driver: ComposeDriver):
        container_name_without_instance_num = driver.project_name + '_' + service_name + '_'

        for name, state in self.get_containers_state(driver).items():
            if name.startswith(container_name_without_instance_num) and state is True:
                self.fail('"%s" is running, but should not' % name)

    def assertLocalRegistryHasImage(self, image_name):
        self.assertIn(image_name, self.get_locally_pulled_docker_images(),
                      msg='Expected that "docker images" will contain image "%s"' % image_name)

    def assertLocalRegistryHasNoPulledImage(self, image_name):
        self.assertNotIn(image_name, self.get_locally_pulled_docker_images(),
                         msg='Expected that "docker images" will not contain image "%s"' % image_name)
