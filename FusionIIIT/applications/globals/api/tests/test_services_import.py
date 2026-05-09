from django.test import SimpleTestCase


class ApiServiceImportTests(SimpleTestCase):
    def test_services_module_imports(self):
        from applications.globals.api import services  # noqa: F401

    def test_selectors_module_imports(self):
        from applications.globals.api import selectors  # noqa: F401
