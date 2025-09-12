from django.urls import path

from . import views
from . import analytics_views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("invallers/", views.invaller_matches, name="invaller_matches"),
    path("<int:pk>/", views.event_detail, name="detail"),
    path("nieuw/", views.event_create, name="create"),
    path("<int:pk>/bewerken/", views.event_edit, name="edit"),
    path("<int:pk>/verwijderen/", views.event_delete, name="delete"),
    path("<int:pk>/aanwezigheid/", views.admin_attendance, name="admin_attendance"),
    path(
        "<int:pk>/aanwezigheid/bulk/",
        views.admin_bulk_attendance,
        name="admin_bulk_attendance",
    ),
    path(
        "<int:pk>/statistiek/<int:stat_id>/verwijderen/",
        views.delete_statistic,
        name="delete_statistic",
    ),
    path("export/calendar.ics", views.export_ics, name="export_ics"),
    path("analytics/", analytics_views.analytics_dashboard, name="analytics"),
]
