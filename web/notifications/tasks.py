"""
Celery tasks for automatic notifications.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from events.models import Event

from notifications.models import AutomaticReminderLog
from notifications.utils import send_event_reminder_notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_automatic_event_reminders(self, reminder_type: str = "1_week"):
    """
    Send automatic reminders for upcoming events.

    Args:
        reminder_type: Type of reminder ('1_week', '3_days', '1_day')
    """
    # Map reminder types to days before event
    days_mapping = {
        "1_week": 7,
        "3_days": 3,
        "1_day": 1,
    }

    days_before = days_mapping.get(reminder_type, 7)

    # Calculate target date (events that are exactly X days from now)
    now = timezone.now()
    target_date_start = now + timedelta(days=days_before)
    target_date_end = target_date_start + timedelta(hours=23, minutes=59, seconds=59)

    logger.info(
        f"Checking for events between {target_date_start} and {target_date_end} for {reminder_type} reminders"
    )

    # Get upcoming events that need reminders
    upcoming_events = Event.objects.filter(
        date__gte=target_date_start,
        date__lte=target_date_end,
        date__gt=now,  # Only future events
    ).exclude(
        automatic_reminders__reminder_type=reminder_type  # Exclude events that already have this reminder sent
    )

    total_events = upcoming_events.count()
    successful_reminders = 0
    failed_reminders = 0

    logger.info(f"Found {total_events} events needing {reminder_type} reminders")

    for event in upcoming_events:
        try:
            with transaction.atomic():
                # Send the reminder
                send_event_reminder_notification(event, days_before=days_before)

                # Log the successful reminder
                AutomaticReminderLog.objects.create(
                    event=event,
                    reminder_type=reminder_type,
                    recipients_count=get_reminder_recipients_count(event),
                    success=True,
                )

                successful_reminders += 1
                logger.info(
                    f"Successfully sent {reminder_type} reminder for event: {event.name}"
                )

        except Exception as e:
            # Log the failed reminder
            try:
                AutomaticReminderLog.objects.create(
                    event=event,
                    reminder_type=reminder_type,
                    recipients_count=0,
                    success=False,
                    error_message=str(e),
                )
            except Exception as log_error:
                logger.error(
                    f"Failed to log reminder failure for event {event.pk}: {log_error}"
                )

            failed_reminders += 1
            logger.error(
                f"Failed to send {reminder_type} reminder for event {event.name}: {str(e)}"
            )

    result_message = (
        f"Automatic {reminder_type} reminders completed: "
        f"{successful_reminders} successful, {failed_reminders} failed out of {total_events} total events"
    )

    logger.info(result_message)

    # If there were failures and we haven't exceeded retry limit, retry
    if failed_reminders > 0 and self.request.retries < self.max_retries:
        logger.info(
            f"Retrying task due to {failed_reminders} failures (attempt {self.request.retries + 1})"
        )
        raise self.retry(countdown=300)  # Retry after 5 minutes

    return {
        "reminder_type": reminder_type,
        "total_events": total_events,
        "successful": successful_reminders,
        "failed": failed_reminders,
        "message": result_message,
    }


def get_reminder_recipients_count(event) -> int:
    """
    Get the count of recipients who would receive a reminder for this event.
    This mimics the logic in send_event_reminder_notification.
    """
    try:
        from attendance.models import Attendance
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get players who haven't submitted their attendance yet
        responded_user_ids = Attendance.objects.filter(event=event).values_list(
            "user_id", flat=True
        )

        active_players = (
            User.objects.filter(is_active=True, email__isnull=False)
            .exclude(email="")
            .exclude(id__in=responded_user_ids)
        )

        # Count valid email addresses
        return sum(1 for player in active_players if player.email)

    except Exception as e:
        logger.error(f"Error counting reminder recipients for event {event.pk}: {e}")
        return 0


@shared_task(bind=True)
def cleanup_old_reminder_logs(self, days_to_keep: int = 90):
    """
    Clean up old automatic reminder logs to prevent database bloat.

    Args:
        days_to_keep: Number of days to keep logs (default: 90)
    """
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)

    deleted_count, _ = AutomaticReminderLog.objects.filter(
        sent_at__lt=cutoff_date
    ).delete()

    logger.info(
        f"Cleaned up {deleted_count} automatic reminder logs older than {days_to_keep} days"
    )

    return {
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
        "days_to_keep": days_to_keep,
    }
