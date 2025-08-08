from django.urls import URLPattern, URLResolver, path

from . import views

app_name = "attendance"

urlpatterns: list[URLPattern | URLResolver] = [
    path("mark/<int:event_id>/", views.mark_attendance, name="mark"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("toggle/<int:event_id>/", views.toggle_attendance, name="toggle"),
    path("set/<int:event_id>/", views.set_attendance, name="set"),
]
