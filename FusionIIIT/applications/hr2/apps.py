from django.apps import AppConfig


class Hr2Config(AppConfig):
    name = 'applications.hr2'

    def ready(self):
        import applications.hr2.signals  # noqa: F401
