"""
Additional security middleware for the RAP application.
"""

import logging

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("rap_web.security")


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add additional security headers to all responses.
    """

    def process_response(self, request, response):
        # Add security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), "
            "accelerometer=(), gyroscope=()"
        )

        # Add HSTS header for HTTPS
        if request.is_secure():
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Log security-relevant events and suspicious activities.
    """

    def process_request(self, request):
        # Log suspicious request patterns
        suspicious_patterns = [
            "union select",
            "drop table",
            "<script>",
            "javascript:",
            "eval(",
            "alert(",
            "../../../",
            "..\\..\\..\\",
            "cmd.exe",
            "/bin/sh",
            "wget ",
            "curl ",
            ".env",
            "wp-admin",
            "phpmyadmin",
            "admin.php",
        ]

        # Check URL path and query string
        full_path = request.get_full_path().lower()
        for pattern in suspicious_patterns:
            if pattern in full_path:
                logger.warning(
                    f"Suspicious request pattern detected: {pattern} "
                    f"from IP {self.get_client_ip(request)} "
                    f"to {request.path}"
                )
                break

        # Log POST data for authentication endpoints
        if request.method == "POST" and any(
            path in request.path for path in ["/users/login/", "/users/register/"]
        ):
            logger.info(
                f"Authentication attempt from IP {self.get_client_ip(request)} "
                f'to {request.path} with user-agent: {request.META.get("HTTP_USER_AGENT", "Unknown")}'
            )

    def process_response(self, request, response):
        # Log failed authentication attempts
        if request.path in [
            "/users/login/",
            "/users/register/",
        ] and response.status_code in [400, 401, 403]:
            logger.warning(
                f"Failed authentication attempt from IP {self.get_client_ip(request)} "
                f"to {request.path} - Status: {response.status_code}"
            )

        return response

    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip


class BasicRateLimitMiddleware(MiddlewareMixin):
    """
    Basic rate limiting middleware as fallback when django-ratelimit is not available.
    """

    def process_request(self, request):
        if (
            not hasattr(settings, "ENABLE_BASIC_RATE_LIMITING")
            or not settings.ENABLE_BASIC_RATE_LIMITING
        ):
            return None

        client_ip = self.get_client_ip(request)

        # Rate limit login attempts
        if request.path == "/users/login/" and request.method == "POST":
            cache_key = f"login_attempts_{client_ip}"
            attempts = cache.get(cache_key, 0)

            if attempts >= 5:  # Max 5 attempts per 5 minutes
                logger.warning(
                    f"Rate limit exceeded for login attempts from IP {client_ip}"
                )
                return HttpResponse(
                    "Te veel inlogpogingen. Probeer het over 5 minuten opnieuw.",
                    status=429,
                )

            cache.set(cache_key, attempts + 1, 300)  # 5 minutes

        # Rate limit registration attempts
        if request.path == "/users/register/" and request.method == "POST":
            cache_key = f"register_attempts_{client_ip}"
            attempts = cache.get(cache_key, 0)

            if attempts >= 3:  # Max 3 attempts per hour
                logger.warning(
                    f"Rate limit exceeded for registration attempts from IP {client_ip}"
                )
                return HttpResponse(
                    "Te veel registratiepogingen. Probeer het over 1 uur opnieuw.",
                    status=429,
                )

            cache.set(cache_key, attempts + 1, 3600)  # 1 hour

        return None

    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip


class AdminAccessControlMiddleware(MiddlewareMixin):
    """
    Additional access control for admin areas.
    """

    def process_request(self, request):
        # Extra security for admin URLs
        if request.path.startswith("/admin/") or request.path.startswith(
            "/users/admin/"
        ):
            # Get user safely (might not be available if auth middleware hasn't run)
            user = getattr(request, "user", None)
            username = getattr(user, "username", "anonymous") if user else "anonymous"

            # Log all admin access attempts
            logger.info(
                f"Admin area access from IP {self.get_client_ip(request)} "
                f"by user {username} to {request.path}"
            )

            # Check for suspicious admin access patterns (only if user is available)
            if user is not None:
                if not user.is_authenticated:
                    logger.warning(
                        f"Unauthenticated access attempt to admin area from IP {self.get_client_ip(request)}"
                    )
                elif not user.is_staff and request.path.startswith("/admin/"):
                    logger.warning(
                        f"Non-staff user {user} attempted to access Django admin from IP {self.get_client_ip(request)}"
                    )

        return None

    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
