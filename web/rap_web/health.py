import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    """Cheap public liveness probe; dependency status belongs in readiness."""
    return JsonResponse({"status": "healthy"})


def _database_ready():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        logger.exception("Database readiness probe failed")
        return False


def _cache_ready():
    try:
        cache_key = "health:readiness"
        cache.set(cache_key, "ok", timeout=10)
        return cache.get(cache_key) == "ok"
    except Exception:
        logger.exception("Cache readiness probe failed")
        return False


@staff_member_required
@require_GET
def readiness_check(request):
    """Authenticated dependency probe with no sensitive diagnostic details."""
    components = {
        "database": "healthy" if _database_ready() else "unhealthy",
        "cache": "healthy" if _cache_ready() else "unhealthy",
    }
    healthy = all(status == "healthy" for status in components.values())
    return JsonResponse(
        {"status": "healthy" if healthy else "unhealthy", "components": components},
        status=200 if healthy else 503,
    )
