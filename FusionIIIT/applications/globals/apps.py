from django.apps import AppConfig


class GlobalsConfig(AppConfig):
    name = 'applications.globals'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import applications.globals.signals  # noqa

