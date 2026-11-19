from django.test import RequestFactory, TestCase, override_settings
from django.views.defaults import server_error

# Production serves static files through the manifest storage with DEBUG off. Under it, a
# {% static %} name missing from the manifest raises, so an error page that used one crashed.
PRODUCTION_LIKE = dict(
    DEBUG=False,
    STATICFILES_STORAGE='whitenoise.storage.CompressedManifestStaticFilesStorage',
)


@override_settings(**PRODUCTION_LIKE)
class ErrorPageTests(TestCase):
    """Unknown URLs get Fusion's 404 page, and server errors its 500 page, instead of a crash."""

    def test_unknown_url_renders_the_404_page(self):
        for path in ('/no-such-page/', '/api/no-such-endpoint/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)
                self.assertContains(response, 'Page not found', status_code=404)

    def test_server_error_renders_the_500_page(self):
        response = server_error(RequestFactory().get('/anything/'))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Something went wrong', response.content)
