from django.apps import AppConfig


class GlobalsConfig(AppConfig):
    name = 'applications.globals'

    def ready(self):
        import applications.globals.signals  # noqa: F401
