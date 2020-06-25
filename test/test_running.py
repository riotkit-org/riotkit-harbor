from rkd.contract import ExecutionContext
from rkd.syntax import TaskDeclaration
from harbor.test import BaseHarborTestClass
from harbor.tasks.running import UpgradeTask
from harbor.tasks.running import StopAndRemoveTask
from harbor.tasks.running import RestartTask
from harbor.exception import ProfileNotFoundException


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

        self.assertEqual([':harbor:pull', ':harbor:start', ':harbor:prod:gateway:reload'], called_tasks_in_order)

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

        args = list(map(lambda call: ' '.join(call[0]).strip(),recorded_calls))
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

    def test_stop_task_executes_stopping_in_order(self):
        pass

    def test_start_task_executes_tasks_startup_in_order(self):
        pass

    def test_start_task_on_single_failure_continues_but_returns_false_at_the_end(self):
        pass
