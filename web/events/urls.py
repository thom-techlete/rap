from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("nieuw/", views.event_create, name="create"),
    path("<int:pk>/bewerken/", views.event_edit, name="edit"),
    path("<int:pk>/verwijderen/", views.event_delete, name="delete"),
    path("<int:pk>/aanwezigheid/", views.admin_attendance, name="admin_attendance"),
    path(
        "<int:pk>/aanwezigheid/bulk/",
        views.admin_bulk_attendance,
        name="admin_bulk_attendance",
    ),
]
