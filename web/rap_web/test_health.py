import json

from django.test import Client, TestCase


class HealthEndpointTests(TestCase):
    def test_public_health_endpoint_returns_only_liveness_status(self):
        response = Client().get("/health/", headers={"host": "localhost"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"status": "healthy"})

    def test_readiness_endpoint_requires_staff_authentication(self):
        response = Client().get("/readiness/", headers={"host": "localhost"})

        self.assertEqual(response.status_code, 302)
