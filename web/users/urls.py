from django.contrib.auth import views as auth_views
from django.urls import URLPattern, URLResolver, path, reverse_lazy

from . import views

app_name = "users"

urlpatterns: list[URLPattern | URLResolver] = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path(
        "logout/", auth_views.LogoutView.as_view(next_page="users:login"), name="logout"
    ),
    # Password reset workflow (forgot credentials)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            email_template_name="users/password_reset_email.txt",
            html_email_template_name="users/password_reset_email.html",
            subject_template_name="users/password_reset_subject.txt",
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    # Admin dashboard routes
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/players/", views.admin_players, name="admin_players"),
    path(
        "admin/players/<int:player_id>/",
        views.admin_player_detail,
        name="admin_player_detail",
    ),
    path("admin/events/", views.admin_events, name="admin_events"),
    path("admin/invitations/", views.admin_invitations, name="admin_invitations"),
    path(
        "admin/invitations/<int:invitation_id>/toggle/",
        views.admin_toggle_invitation,
        name="admin_toggle_invitation",
    ),
    path(
        "admin/bulk-edit-positions/",
        views.admin_bulk_edit_positions,
        name="admin_bulk_edit_positions",
    ),
]
