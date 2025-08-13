from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin


class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Require authentication for all views except a strict allowlist.

    Publicly accessible:
    - Users auth routes: login, register, logout
    - Health check endpoint for monitoring
    - Static files under STATIC_URL
    """

    # Names of URL patterns that can be accessed without authentication
    EXEMPT_URL_NAMES: set[str] = {
        "users:login",
        "users:register",
        "users:logout",
        "health_check",  # Health endpoint for monitoring
    }

    # Path prefixes that should be publicly accessible
    EXEMPT_PATH_PREFIXES: tuple[str, ...] = (settings.STATIC_URL,)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponse],
        view_args: list[Any],
        view_kwargs: dict[str, Any],
    ) -> HttpResponse | None:
        # Already authenticated -> allow
        if request.user.is_authenticated:
            return None

        # Allow static assets
        path: str = request.path
        if any(
            path.startswith(prefix) for prefix in self.EXEMPT_PATH_PREFIXES if prefix
        ):
            return None

        # Resolve the URL name and namespace if possible
        try:
            match = resolve(path)
            url_name = match.view_name  # includes namespace like 'users:login'
        except Exception:
            url_name = None

        # Allow explicitly exempt URL names
        if url_name and url_name in self.EXEMPT_URL_NAMES:
            return None

        # Otherwise redirect to login
        return redirect_to_login(next=path, login_url=settings.LOGIN_URL)
