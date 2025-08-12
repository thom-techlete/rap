"""
Django management command to send automatic event reminders.
Useful for testing and manual execution.
"""

from django.core.management.base import BaseCommand

from notifications.tasks import send_automatic_event_reminders


class Command(BaseCommand):
    help = "Send automatic event reminders for upcoming events"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            choices=["1_week", "3_days", "1_day"],
            default="1_week",
            help="Type of reminder to send (default: 1_week)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually sending emails",
        )

    def handle(self, *args, **options):
        reminder_type = options["type"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would send {reminder_type} reminders")
            )

            # Import here to avoid circular imports
            from datetime import timedelta

            from django.utils import timezone
            from events.models import Event

            # Map reminder types to days before event
            days_mapping = {
                "1_week": 7,
                "3_days": 3,
                "1_day": 1,
            }

            days_before = days_mapping.get(reminder_type, 7)

            # Calculate target date
            now = timezone.now()
            target_date_start = now + timedelta(days=days_before)
            target_date_end = target_date_start + timedelta(
                hours=23, minutes=59, seconds=59
            )

            # Get upcoming events that would need reminders
            upcoming_events = Event.objects.filter(
                date__gte=target_date_start, date__lte=target_date_end, date__gt=now
            ).exclude(automatic_reminders__reminder_type=reminder_type)

            self.stdout.write(
                f"Target date range: {target_date_start.strftime('%d-%m-%Y %H:%M')} to {target_date_end.strftime('%d-%m-%Y %H:%M')}"
            )
            self.stdout.write(
                f"Found {upcoming_events.count()} events that would receive {reminder_type} reminders:"
            )

            for event in upcoming_events:
                self.stdout.write(
                    f"  - {event.name} on {event.date.strftime('%d-%m-%Y %H:%M')}"
                )

            if not upcoming_events.exists():
                self.stdout.write(
                    self.style.SUCCESS("No events found that need reminders.")
                )
        else:
            self.stdout.write(f"Sending {reminder_type} reminders...")

            try:
                # Execute the task synchronously for management command
                result = send_automatic_event_reminders(reminder_type=reminder_type)

                if result:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully completed: {result['successful']} sent, "
                            f"{result['failed']} failed out of {result['total_events']} events"
                        )
                    )
                else:
                    self.stdout.write(self.style.ERROR("Task returned no result"))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error executing reminder task: {str(e)}")
                )
