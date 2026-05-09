from django.apps import AppConfig


class FileTrackingConfig(AppConfig):
    name = 'applications.filetracking'

    def ready(self):
        """Register signals when app is ready"""
        import applications.filetracking.signals  # noqa: F401
