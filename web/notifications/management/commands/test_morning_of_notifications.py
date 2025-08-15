from django.core.management.base import BaseCommand, CommandError
from events.models import Event

from notifications import tasks as notification_tasks
from notifications.utils import send_morning_of_notification


class Command(BaseCommand):
    help = "Test morning-of notifications. Use --sync to run synchronously or provide --event-id to test a specific event."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Run the task synchronously in-process instead of sending to Celery",
        )
        parser.add_argument(
            "--event-id",
            type=int,
            help="ID of a specific event to test the notification for",
        )

    def handle(self, *args, **options):
        event_id = options.get("event_id")
        run_sync = options.get("sync")

        if event_id:
            try:
                event = Event.objects.get(pk=event_id)
            except Event.DoesNotExist as err:
                raise CommandError(f"Event with id {event_id} does not exist") from err

            self.stdout.write(
                self.style.NOTICE(
                    f"Testing morning-of notification for event: {event.name} (id={event.pk})"
                )
            )

            if run_sync:
                sent = send_morning_of_notification(event)
                self.stdout.write(
                    self.style.SUCCESS(f"Synchronous test complete, recipients: {sent}")
                )
            else:
                # Queuing a task for a single event is not supported by the current Celery task.
                # Queueing the general morning-of task will process all today's events instead.
                self.stdout.write(
                    self.style.WARNING(
                        "Async per-event processing is not supported; queuing general morning-of task for all events today"
                    )
                )
                res = notification_tasks.send_event_summary_to_attendees.apply_async(
                    kwargs={"reminder_type": "morning_of"}
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Queued morning-of notifications task (id={res.id})"
                    )
                )

        else:
            # No event specified: run task for today's events
            self.stdout.write(
                self.style.NOTICE("Running morning-of notifications for today's events")
            )
            if run_sync:
                # Call the task synchronously using apply (runs in-process)
                result = notification_tasks.send_event_summary_to_attendees.apply(
                    kwargs={"reminder_type": "morning_of"}
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Synchronous run complete: {result.result}")
                )
            else:
                res = notification_tasks.send_event_summary_to_attendees.apply_async(
                    kwargs={"reminder_type": "morning_of"}
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Queued morning-of notifications task (id={res.id})"
                    )
                )
