import os
import subprocess
from tempfile import NamedTemporaryFile
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.gateway import ForceReloadSSLTask


class TestForceReloadSSLTask(BaseHarborTestClass):
    def test_functional_force_reload_is_triggered_when_ssl_is_not_disabled(self):
        """We can only check if the container is taking the query

        Checks:
            - Required containers will be bringed up
            - Script will be triggered
        """

        # 1) Replace a script inside container
        #    As we do not want to trigger real SSL renew script - it would take long and fail anyway as it requires
        #    external service to pass in impossible conditions
        with NamedTemporaryFile(delete=False) as f:
            f.write('''#!/bin/bash
            echo "Renewing certificates..."
            exit 0
            '''.encode('utf-8'))

        subprocess.call(['chmod', '+x', f.name])

        self.mock_compose({
            'services': {
                'gateway_letsencrypt': {
                    'volumes': [
                        f.name + ':/app/force_renew'
                    ]
                }
            }
        })

        try:
            # 2) Test
            out = self.execute_task(ForceReloadSSLTask(), args={}, env={'DISABLE_SSL': ''})
            self.assertIn('Renewing certificates...', out)
        finally:
            subprocess.check_call('docker logs env_simple_gateway_letsencrypt_1', shell=True)

            self.remove_all_containers()
            os.unlink(f.name)

    def test_functional_ssl_regeneration_is_not_triggered_when_ssl_is_disabled(self):
        """Checks that SSL container will not be touched, when DISABLE_SSL=true
        """

        out = self.execute_task(ForceReloadSSLTask(), args={}, env={'DISABLE_SSL': 'true'})
        self.assertIn('not regenerating anything', out)
