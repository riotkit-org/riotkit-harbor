from subprocess import CalledProcessError
from rkd.api.contract import ExecutionContext
from rkd.api.syntax import TaskDeclaration
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.running import UpgradeTask
from rkd_harbor.tasks.running import StopAndRemoveTask
from rkd_harbor.tasks.running import StopTask
from rkd_harbor.tasks.running import StartTask
from rkd_harbor.tasks.running import RestartTask
from rkd_harbor.exception import ProfileNotFoundException


class TestRunning(BaseHarborTestClass):
    """Set of functional tests for :start, :stop, :restart, :upgrade"""

    def test_upgrade_calls_tasks_in_order(self):
        """Assert that :upgrade calls other Harbor tasks in fixed order"""

        task = UpgradeTask()
        recorded_calls = []
        task.rkd = lambda *args, **kwags: recorded_calls.append(args)

        self.execute_task(task, args={
            '--profile': 'profile1',
            '--strategy': 'recreate',
            '--remove-previous-images': False
        })

        called_tasks_in_order = list(filter(
            lambda element: element.startswith(':'),
            recorded_calls[0][0]
        ))

        self.assertEqual([':harbor:templates:render', ':harbor:pull', ':harbor:start', ':harbor:gateway:reload'], called_tasks_in_order)

    def test_upgrade_calls_tasks_with_proper_arguments(self):
        """Check if arguments such as --profile and --strategy are passed"""

        task = UpgradeTask()
        recorded_calls = []
        task.rkd = lambda *args, **kwags: recorded_calls.append(args)

        self.execute_task(task, args={
            '--profile': 'profile1',
            '--strategy': 'recreate',
            '--remove-previous-images': False
        })

        args = ' '.join(recorded_calls[0][0])

        self.assertIn(':harbor:pull --profile=profile1', args)
        self.assertIn(':harbor:start --profile=profile1 --strategy=recreate', args)

    def test_stop_and_remove_task_reports_invalid_profile(self):
        task = StopAndRemoveTask()
        recorded_calls = []
        task.rkd = lambda *args, **kwags: recorded_calls.append(args)

        self.assertRaises(ProfileNotFoundException, lambda: self.execute_task(task, args={
            '--profile': 'non-existing',
            '--strategy': 'recreate',
        }))

    def test_stop_and_remove_task_iterates_through_matched_profiles_and_calls_service_removal(self):
        task = StopAndRemoveTask()
        recorded_calls = []
        task.rkd = lambda *args, **kwags: recorded_calls.append(args)

        self.execute_task(task, args={
            '--profile': 'profile1',
            '--with-image': False
        })

        args = list(map(lambda call: ' '.join(call[0]).strip(), recorded_calls))
        self.assertEqual([':harbor:service:rm gateway', ':harbor:service:rm website'], args)

    def test_restart_calls_driver_restart_method_on_matched_services(self):
        """Test calls restart on expected services in expected order"""

        task = RestartTask()
        restarted_services = []

        ctx = ExecutionContext(
            TaskDeclaration(task),
            args={},
            env={}
        )
        task.containers(ctx).restart = lambda service_name, args = '': restarted_services.append(service_name)

        self.execute_task(task, args={
            '--profile': 'profile1',
            '--with-image': False
        })

        self.assertEqual(['gateway', 'website'], restarted_services)

    def test_stop_task_executes_stop_task_multiple_times(self):
        """Test that StopTask will call Driver.stop() multiple times"""

        task = StopTask()
        recorded_calls = []

        ctx = ExecutionContext(
            TaskDeclaration(task),
            args={},
            env={}
        )
        task.containers(ctx).stop = lambda service_name, args='', capture = False: recorded_calls.append(service_name)

        self.execute_task(task, args={
            '--profile': ''
        })

        self.assertIn('gateway', recorded_calls)
        self.assertIn('gateway_letsencrypt', recorded_calls)
        self.assertIn('gateway_proxy_gen', recorded_calls)

    def test_start_task_executes_tasks_startup_in_order(self):
        """Basic test to check if profile is considered, and if startup order is preserved"""

        task = StartTask()
        recorded_calls = []
        task.rkd = lambda *args, **kwags: recorded_calls.append(args)

        self.execute_task(task, args={
            '--profile': 'profile1',
            '--strategy': 'rolling',
            '--remove-previous-images': False
        })

        args = list(map(lambda call: ' '.join(call[0]).strip(), recorded_calls))
        commandline = ' '.join(args).replace('  ', ' ').strip()

        self.assertEqual(
            '--no-ui :harbor:service:up gateway --strategy=rolling --no-ui :harbor:service:up website --strategy=rolling',
            commandline
        )

    def test_start_task_on_single_failure_continues_but_returns_false_at_the_end(self):
        """Checks that even if one service was not started correctly, it will not break up whole deployment
        The next services should start normally, but the result at the end should be a 'failure'"""

        task = StartTask()
        recorded_calls = []

        def rkd_mock(*args, **kwargs):
            if len(recorded_calls) == 0:
                recorded_calls.append(args)
                raise CalledProcessError(1, 'bash')

            recorded_calls.append(args)

        task.rkd = rkd_mock

        out = self.execute_task(task, args={
            '--profile': 'profile1',
            '--strategy': 'rolling',
            '--remove-previous-images': False
        })

        self.assertIn('Cannot start service "gateway"', out)
        self.assertIn('Service "website" was started', out)
        self.assertIn('TASK_EXIT_RESULT=False', out)
