from subprocess import CalledProcessError
from rkd_harbor.test import BaseHarborTestClass
from rkd_harbor.tasks.repositories import FetchRepositoryTask
from rkd_harbor.tasks.repositories import ListRepositoriesTask
from rkd_harbor.tasks.repositories import FetchAllRepositories


class TestRepositories(BaseHarborTestClass):
    def test_functional_repository_is_cloned_then_pulled(self):
        """Scenario: Clone repository, then try to clone again - it should end with a pull of existing repository

        Additionally checks that pre_update() and post_update() hooks are executed.
        """

        with self.subTest('Test clone'):
            out = self.execute_task(FetchRepositoryTask(), args={'name': 'example'})
            self.assertIn('Cloning into', out)
            self.assertIn('TASK_EXIT_RESULT=True', out)

            # verify that hooks were executed at all
            self.assertIn('Starting to clone/pull example repository :)', out)
            self.assertIn("I'm a post_update hook", out)

        with self.subTest('Test checkout'):
            out = self.execute_task(FetchRepositoryTask(), args={'name': 'example'})
            self.assertIn('Already up to date', out)
            self.assertIn('TASK_EXIT_RESULT=True', out)

            # verify that hooks were executed at all
            self.assertIn('Starting to clone/pull example repository :)', out)
            self.assertIn("I'm a post_update hook", out)

    def test_will_not_perform_action_for_unknown_application_and_return_meaningful_error(self):
        """Check that application name is validated, and a tip is displayed with an expected path to the configuration
        file"""

        out = self.execute_task(FetchRepositoryTask(), args={'name': 'not_working'})

        self.assertIn('Cannot pull a repository: Unknown application', out)
        self.assertIn('repos-enabled/not_working.sh" file not found', out)

    def test_repository_listing_shows_example_application_repository(self):
        """Assert that example data appears"""

        out = self.execute_task(ListRepositoriesTask(), args={})

        self.assertIn('Configured GIT repository', out)
        self.assertIn('example', out)
        self.assertIn('second', out)

    def test_fetch_all_repositories_is_skipping_failures_and_keeping_going_on_but_producing_a_failure_at_the_end(self):
        """Check that FetchAllRepositories() is fetching all repositories one-by-one, ignoring a failure,
        but marking the whole operation as failed if at least one repository failed to update"""

        collected_args = []
        task = FetchAllRepositories()

        def mocked_rkd(*args, **kwargs):
            if len(collected_args) == 0:
                collected_args.append(list(args)[0])
                raise CalledProcessError(returncode=128, cmd='Hello, this method was mocked ;)')

            collected_args.append(list(args)[0])

        task.rkd = mocked_rkd
        out = self.execute_task(task, args={})

        # check logging
        self.assertIn('Updating "example"', out)
        self.assertIn('Updating "second"', out)
        self.assertIn('Failed updating "example"', out)
        self.assertIn('TASK_EXIT_RESULT=False', out)

        self.assertEqual(
            [[':harbor:git:apps:update', 'example'], [':harbor:git:apps:update', 'second']],
            collected_args
        )
