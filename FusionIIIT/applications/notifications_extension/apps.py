from django.apps import AppConfig


class NotificationConfig(AppConfig):
    name = "applications.notifications_extension"
    label = "notifications_extension"
    verbose_name = "Notification"

    def ready(self):
        pass
