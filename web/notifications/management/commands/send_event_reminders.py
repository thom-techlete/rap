from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event

from notifications.utils import send_event_reminder_notification


class Command(BaseCommand):
    help = "Send reminder emails for upcoming events"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Number of days before the event to send reminders (default: 1)",
        )
        parser.add_argument(
            "--event-id", type=int, help="Send reminder for specific event ID only"
        )

    def handle(self, *args, **options):
        days_before = options["days"]
        event_id = options.get("event_id")

        if event_id:
            # Send reminder for specific event
            try:
                event = Event.objects.get(id=event_id)
                self.stdout.write(f"Sending reminder for event: {event.name}")
                send_event_reminder_notification(event, days_before)
                self.stdout.write(
                    self.style.SUCCESS(f"Reminder sent for event: {event.name}")
                )
            except Event.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Event with ID {event_id} not found")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to send reminder: {str(e)}")
                )
        else:
            # Send reminders for all upcoming events within the specified timeframe
            target_date = timezone.now() + timezone.timedelta(days=days_before)

            # Get events that are exactly X days away (within a 24-hour window)
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timezone.timedelta(days=1)

            upcoming_events = Event.objects.filter(
                date__gte=start_date, date__lt=end_date
            )

            if not upcoming_events.exists():
                self.stdout.write(
                    self.style.WARNING(f"No events found {days_before} days from now")
                )
                return

            self.stdout.write(
                f"Found {upcoming_events.count()} events {days_before} days from now"
            )

            success_count = 0
            error_count = 0

            for event in upcoming_events:
                try:
                    self.stdout.write(f"Sending reminder for: {event.name}")
                    send_event_reminder_notification(event, days_before)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Reminder sent for: {event.name}")
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Failed to send reminder for {event.name}: {str(e)}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Reminder process complete: {success_count} successful, {error_count} failed"
                )
            )
