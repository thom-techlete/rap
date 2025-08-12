import uuid
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event

from notifications.utils import send_bulk_notifications


class Command(BaseCommand):
    help = "Test recurring event notification by creating a test series"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email address to send the test notification to",
        )

    def handle(self, *args, **options):
        to_email = options["email"]

        # Create a test recurring event series
        base_date = timezone.now() + timedelta(days=7)  # Start next week
        recurring_link_id = uuid.uuid4()  # Generate proper UUID

        # Create test events
        events = []
        for i in range(4):  # Create 4 weekly events
            event_date = base_date + timedelta(weeks=i)
            event = Event.objects.create(
                name=f"Test Training {i+1}",
                description="Dit is een test herhalend evenement voor de notificatie functionaliteit.",
                event_type="training",
                date=event_date,
                location="Sportpark De Test",
                is_mandatory=False,
                recurring_event_link_id=recurring_link_id,
                recurrence_type="weekly",
                recurrence_end_date=(base_date + timedelta(weeks=3)).date(),
            )
            events.append(event)

        self.stdout.write(
            self.style.SUCCESS(f"Created {len(events)} test recurring events")
        )

        # Test the notification system
        try:
            # Temporarily update the first user's email to the test email
            from django.contrib.auth import get_user_model

            User = get_user_model()

            # Get or create a test user
            test_user, created = User.objects.get_or_create(
                username="test_notification_user",
                defaults={
                    "email": to_email,
                    "first_name": "Test",
                    "last_name": "User",
                    "is_active": True,
                },
            )

            if not created:
                test_user.email = to_email
                test_user.is_active = True
                test_user.save()

            # Send the notification
            success_count, error_count = send_bulk_notifications(events, "new_event")

            if error_count == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Test recurring event notification sent successfully to {to_email}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send test notification: {error_count} errors"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error sending test notification: {str(e)}")
            )

        # Clean up - delete the test events
        self.stdout.write("Cleaning up test events...")
        for event in events:
            event.delete()

        self.stdout.write(self.style.SUCCESS("Test completed and cleaned up"))
