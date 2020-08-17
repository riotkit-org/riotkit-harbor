from rkd_harbor.test import BaseHarborTestClass


class TestRedirectToWWWFeature(BaseHarborTestClass):
    """Functional tests to check NGINX template feature - redirection from WWW to non-WWW hostname

    It's about a label: `org.riotkit.redirectFromWWW: true`
    """

    def test_redirects_from_www_to_non_www(self):
        """Verifies that there is a redirection www.nginx-redirect-to-www.local -> nginx-redirect-to-www.local"""

        drv = self._get_prepared_compose_driver()
        self.prepare_service_discovery(drv)
        self.prepare_example_service('website_with_redirect_to_www', uses_service_discovery=True)

        content = self.fetch_page_content('www.nginx-redirect-to-www.local')

        self.assertIn('Location: http://nginx-redirect-to-www.local', content)
        self.assertIn('HTTP/1.1 302', content)
