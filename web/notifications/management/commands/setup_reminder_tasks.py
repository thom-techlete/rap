"""
Django management command to create default periodic tasks for automatic reminders.
Run this once to set up the default schedule in the admin interface.
"""

import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create default periodic tasks for automatic event reminders"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing tasks if they exist",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]

        # Create or get schedules
        daily_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=9,  # 9:00 AM
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
            defaults={"timezone": "Europe/Amsterdam"},
        )

        weekly_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,  # 2:00 AM
            day_of_week=1,  # Monday
            day_of_month="*",
            month_of_year="*",
            defaults={"timezone": "Europe/Amsterdam"},
        )

        # Define default tasks
        tasks_to_create = [
            {
                "name": "1-week Event Reminders",
                "task": "notifications.tasks.send_automatic_event_reminders",
                "crontab": daily_schedule,
                "kwargs": json.dumps({"reminder_type": "1_week"}),
                "enabled": True,
                "description": "Send automatic reminders 1 week before events",
            },
            {
                "name": "3-day Event Reminders",
                "task": "notifications.tasks.send_automatic_event_reminders",
                "crontab": daily_schedule,
                "kwargs": json.dumps({"reminder_type": "3_days"}),
                "enabled": False,  # Disabled by default
                "description": "Send automatic reminders 3 days before events",
            },
            {
                "name": "1-day Event Reminders",
                "task": "notifications.tasks.send_automatic_event_reminders",
                "crontab": daily_schedule,
                "kwargs": json.dumps({"reminder_type": "1_day"}),
                "enabled": False,  # Disabled by default
                "description": "Send automatic reminders 1 day before events",
            },
            {
                "name": "Cleanup Old Reminder Logs",
                "task": "notifications.tasks.cleanup_old_reminder_logs",
                "crontab": weekly_schedule,
                "kwargs": json.dumps({"days_to_keep": 90}),
                "enabled": True,
                "description": "Clean up automatic reminder logs older than 90 days",
            },
        ]

        created_count = 0
        updated_count = 0

        for task_data in tasks_to_create:
            task_name = task_data["name"]

            # Check if task already exists
            existing_task = PeriodicTask.objects.filter(name=task_name).first()

            if existing_task:
                if overwrite:
                    # Update existing task
                    for key, value in task_data.items():
                        if key != "name":  # Don't update the name
                            setattr(existing_task, key, value)
                    existing_task.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated task: {task_name}"))
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Task already exists: {task_name} (use --overwrite to update)"
                        )
                    )
            else:
                # Create new task
                PeriodicTask.objects.create(**task_data)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created task: {task_name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: {created_count} tasks created, {updated_count} tasks updated"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\nYou can now manage these tasks through the Django admin at:"
            )
        )
        self.stdout.write("  /admin/django_celery_beat/periodictask/")
        self.stdout.write("\nTo customize schedules, edit them at:")
        self.stdout.write("  /admin/django_celery_beat/crontabschedule/")
        self.stdout.write("  /admin/django_celery_beat/intervalschedule/")
