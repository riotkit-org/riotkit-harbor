import os
import subprocess
from tempfile import NamedTemporaryFile
from harbor.test import BaseHarborTestClass
from harbor.tasks.gateway import ForceReloadSSLTask


class TestForceReloadSSLTask(BaseHarborTestClass):
    def test_force_reload_is_triggered_when_ssl_is_not_disabled(self):
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
            os.unlink(f.name)
