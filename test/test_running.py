from harbor.test import BaseHarborTestClass
from harbor.tasks.running import UpgradeTask
from harbor.tasks.running import StopAndRemoveTask
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
