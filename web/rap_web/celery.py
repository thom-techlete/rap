"""
Celery configuration for SV Rap 8 project.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rap_web.settings")

app = Celery("rap_web")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.update(
    timezone="Europe/Amsterdam",
    enable_utc=True,
)

# Task configuration
app.conf.task_always_eager = False
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_expires = 3600  # 1 hour

# Worker configuration
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 1000


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f"Request: {self.request!r}")
