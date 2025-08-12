from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path(
        "send-notification/<int:event_id>/",
        views.send_event_notification,
        name="send_event_notification",
    ),
    path(
        "send-reminder/<int:event_id>/",
        views.send_event_reminder,
        name="send_event_reminder",
    ),
    path("status/", views.notification_status, name="status"),
]
