"""
Django management command to create default schedule configurations.
"""

from django.core.management.base import BaseCommand
from notifications.models import ScheduleConfiguration


class Command(BaseCommand):
    help = "Create default schedule configurations for notification tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing configurations if they exist",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]

        # Define default configurations
        default_configs = [
            {
                "name": "1-week Herinnering",
                "task": "notifications.tasks.send_automatic_event_reminders",
                "reminder_type": "1_week",
                "minute": "0",
                "hour": "9",
                "day_of_week": "*",
                "day_of_month": "*",
                "month_of_year": "*",
                "enabled": True,
            },
            {
                "name": "3-day Herinnering",
                "task": "notifications.tasks.send_automatic_event_reminders",
                "reminder_type": "3_days",
                "minute": "0",
                "hour": "10",
                "day_of_week": "*",
                "day_of_month": "*",
                "month_of_year": "*",
                "enabled": False,  # Disabled by default
            },
            {
                "name": "1-day Herinnering",
                "task": "notifications.tasks.send_automatic_event_reminders",
                "reminder_type": "1_day",
                "minute": "0",
                "hour": "11",
                "day_of_week": "*",
                "day_of_month": "*",
                "month_of_year": "*",
                "enabled": False,  # Disabled by default
            },
            {
                "name": "Wekelijkse Log Opruiming",
                "task": "notifications.tasks.cleanup_old_reminder_logs",
                "reminder_type": "",
                "minute": "0",
                "hour": "2",
                "day_of_week": "1",  # Monday
                "day_of_month": "*",
                "month_of_year": "*",
                "enabled": True,
            },
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for config_data in default_configs:
            name = config_data["name"]
            
            # Check if configuration already exists
            existing = ScheduleConfiguration.objects.filter(name=name).first()
            
            if existing:
                if overwrite:
                    # Update existing configuration
                    for key, value in config_data.items():
                        setattr(existing, key, value)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated configuration: {name}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"Skipped existing configuration: {name}")
                    )
            else:
                # Create new configuration
                ScheduleConfiguration.objects.create(**config_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created configuration: {name}")
                )

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"Created: {created_count}")
        self.stdout.write(f"Updated: {updated_count}")
        self.stdout.write(f"Skipped: {skipped_count}")
        self.stdout.write("="*50)

        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nDefault schedule configurations have been set up successfully!"
                )
            )
            self.stdout.write(
                "You can now manage these configurations in the admin interface:"
            )
            self.stdout.write("- Django Admin: /admin/notifications/scheduleconfiguration/")
            self.stdout.write("- Custom Admin: /notifications/admin/schedule/")
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nNo configurations were created or updated."
                )
            )
            if skipped_count > 0:
                self.stdout.write("Use --overwrite to update existing configurations.")