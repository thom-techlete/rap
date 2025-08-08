from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Health check endpoint for monitoring system status.
    Returns JSON response with status of various components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": str(request.META.get("HTTP_HOST", "unknown")),
        "components": {},
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis connection
    try:
        # Simple cache test
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            health_status["components"]["redis"] = "healthy"
        else:
            health_status["components"]["redis"] = "unhealthy: cache test failed"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Return appropriate HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)
