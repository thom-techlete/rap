from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"
    verbose_name = "Notifications"

    def ready(self):
        # Import celery admin customizations
        import importlib.util

        if importlib.util.find_spec("notifications.celery_admin"):
            pass

    verbose_name = "Notifications"
