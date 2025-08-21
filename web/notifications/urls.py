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
    
    # Admin scheduling URLs
    path("admin/schedule/", views.schedule_admin_dashboard, name="schedule_admin_dashboard"),
    path("admin/schedule/sync/", views.sync_tasks_manual, name="sync_tasks_manual"),
    
    # Push notification URLs
    path("push/subscribe/", views.PushSubscriptionView.as_view(), name="push_subscribe"),
    path("push/test/", views.send_test_notification, name="push_test"),
    path("push/vapid-key/", views.get_vapid_public_key, name="vapid_key"),
    
    # PWA offline page
    path("offline/", views.offline_page, name="offline"),
]
