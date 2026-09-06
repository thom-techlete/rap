import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from rap_web.security_middleware import BasicRateLimitMiddleware


def test_production_uses_shared_redis_cache():
    assert settings.CACHES["default"]["BACKEND"] == (
        "django.core.cache.backends.redis.RedisCache"
    )


def test_axes_lockout_includes_client_ip():
    assert ["username", "ip_address"] in settings.AXES_LOCKOUT_PARAMETERS


def test_ratelimit_uses_verified_client_ip_resolver():
    assert settings.RATELIMIT_IP_META_KEY == (
        "rap_web.security_middleware.get_client_ip"
    )


@override_settings(TRUSTED_PROXY_IPS=["10.0.0.1"])
def test_untrusted_forwarded_for_header_is_ignored():
    request = RequestFactory().get(
        "/",
        HTTP_X_FORWARDED_FOR="203.0.113.9",
        REMOTE_ADDR="198.51.100.7",
    )

    assert BasicRateLimitMiddleware(lambda request: None).get_client_ip(request) == (
        "198.51.100.7"
    )


@override_settings(TRUSTED_PROXY_IPS=["10.0.0.1"])
def test_trusted_forwarded_for_header_is_used():
    request = RequestFactory().get(
        "/",
        HTTP_X_FORWARDED_FOR="203.0.113.9",
        REMOTE_ADDR="10.0.0.1",
    )

    assert BasicRateLimitMiddleware(lambda request: None).get_client_ip(request) == (
        "203.0.113.9"
    )


class PushCsrfTestCase(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="csrf-user",
            email="csrf@example.com",
            password="correct-password-123!",
            is_active=True,
        )
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(user)

    def test_push_subscription_write_requires_csrf(self):
        response = self.client.post(
            reverse("notifications:push_subscribe"),
            data=json.dumps({"subscription": {}}),
            content_type="application/json",
        )

        assert response.status_code == 403

    def test_push_unsubscribe_requires_csrf(self):
        response = self.client.delete(
            reverse("notifications:push_subscribe"),
            data=json.dumps({"endpoint": "https://push.example/endpoint"}),
            content_type="application/json",
        )

        assert response.status_code == 403

    def test_test_notification_requires_csrf(self):
        response = self.client.post(reverse("notifications:push_test"))

        assert response.status_code == 403
