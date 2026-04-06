from django.apps import AppConfig


class NotificationConfig(AppConfig):
    name = 'apps.notification'

    def ready(self):
        """Import signals when the app is ready"""
        import apps.notification.signals  # noqa
