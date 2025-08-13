import os
import time
from datetime import datetime

from celery.app.control import Inspect
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.mail import get_connection
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Comprehensive health check endpoint for monitoring system status.
    Returns JSON response with status of various components.
    """
    start_time = time.time()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {},
        "details": {},
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                health_status["components"]["database"] = "healthy"
                health_status["details"]["database"] = {
                    "engine": settings.DATABASES["default"]["ENGINE"],
                    "name": settings.DATABASES["default"]["NAME"],
                }
            else:
                health_status["components"]["database"] = "unhealthy: unexpected result"
                health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis/Cache connection
    try:
        cache_key = f"health_check_{int(time.time())}"
        cache.set(cache_key, "ok", 10)
        if cache.get(cache_key) == "ok":
            health_status["components"]["cache"] = "healthy"
            health_status["details"]["cache"] = {
                "backend": settings.CACHES["default"]["BACKEND"]
            }
            cache.delete(cache_key)  # Clean up
        else:
            health_status["components"]["cache"] = "unhealthy: cache test failed"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["components"]["cache"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Celery worker status
    try:
        from rap_web.celery import app as celery_app

        inspect = Inspect(app=celery_app)

        # Check if workers are active
        active_workers = inspect.active()
        if active_workers:
            worker_count = len(active_workers)
            health_status["components"]["celery_workers"] = "healthy"
            health_status["details"]["celery_workers"] = {
                "active_workers": worker_count,
                "worker_names": list(active_workers.keys()),
            }
        else:
            health_status["components"][
                "celery_workers"
            ] = "unhealthy: no active workers"
            health_status["status"] = "unhealthy"

        # Check Celery beat scheduler
        scheduled_tasks = inspect.scheduled()
        if scheduled_tasks is not None:
            health_status["components"]["celery_beat"] = "healthy"
            total_scheduled = (
                sum(len(tasks) for tasks in scheduled_tasks.values())
                if scheduled_tasks
                else 0
            )
            health_status["details"]["celery_beat"] = {
                "scheduled_tasks": total_scheduled
            }
        else:
            health_status["components"]["celery_beat"] = "warning: beat status unknown"

    except ImportError:
        health_status["components"]["celery"] = "warning: celery not available"
    except Exception as e:
        health_status["components"]["celery"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check email backend
    try:
        connection_test = get_connection()
        connection_test.open()
        connection_test.close()
        health_status["components"]["email"] = "healthy"
        health_status["details"]["email"] = {
            "backend": settings.EMAIL_BACKEND,
            "host": getattr(settings, "EMAIL_HOST", "not configured"),
        }
    except Exception as e:
        health_status["components"]["email"] = f"unhealthy: {str(e)}"
        # Email issues shouldn't mark the whole system as unhealthy
        # health_status["status"] = "unhealthy"

    # Check file system permissions and directories
    try:
        media_writable = (
            os.access(settings.MEDIA_ROOT, os.W_OK)
            if os.path.exists(settings.MEDIA_ROOT)
            else False
        )
        static_readable = (
            os.access(settings.STATIC_ROOT, os.R_OK)
            if os.path.exists(settings.STATIC_ROOT)
            else True
        )

        if media_writable and static_readable:
            health_status["components"]["filesystem"] = "healthy"
        else:
            health_status["components"]["filesystem"] = "unhealthy: permission issues"
            health_status["status"] = "unhealthy"

        health_status["details"]["filesystem"] = {
            "media_writable": media_writable,
            "static_readable": static_readable,
            "media_root": str(settings.MEDIA_ROOT),
            "static_root": str(settings.STATIC_ROOT),
        }
    except Exception as e:
        health_status["components"]["filesystem"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Django apps
    try:
        critical_apps = ["users", "events", "attendance", "notifications"]
        app_status = {}

        for app_name in critical_apps:
            try:
                apps.get_app_config(app_name)
                app_status[app_name] = "healthy"
            except LookupError:
                app_status[app_name] = "not found"
                health_status["status"] = "unhealthy"

        health_status["components"]["django_apps"] = (
            "healthy"
            if all(status == "healthy" for status in app_status.values())
            else "unhealthy"
        )
        health_status["details"]["django_apps"] = app_status

    except Exception as e:
        health_status["components"]["django_apps"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Add performance metrics
    end_time = time.time()
    health_status["details"]["performance"] = {
        "response_time_ms": round((end_time - start_time) * 1000, 2),
        "debug_mode": settings.DEBUG,
    }

    # Determine overall health status
    unhealthy_components = [
        name
        for name, status in health_status["components"].items()
        if status.startswith("unhealthy")
    ]

    if unhealthy_components:
        health_status["status"] = "unhealthy"
        health_status["unhealthy_components"] = unhealthy_components

    # Return appropriate HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)
