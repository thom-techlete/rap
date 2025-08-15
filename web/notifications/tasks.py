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
from notifications.utils import (
    send_event_reminder_notification,
    send_morning_of_notification,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_automatic_event_reminders(self, reminder_type: str = "1_week"):
    """
    Send automatic reminders for upcoming events.

    Args:
        reminder_type: Type of reminder ('1_week', '3_days', '1_day', 'morning_of').
    """
    # Map reminder types to days before event
    days_mapping = {
        "1_week": 7,
        "3_days": 3,
        "1_day": 1,
        "morning_of": 0,  # Morning of event doesn't use days before
    }

    days_before = days_mapping.get(reminder_type, 7)

    # Calculate target date (events that are exactly X days from now)
    now = timezone.now()
    target_date_start = (now + timedelta(days=days_before)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    target_date_end = target_date_start.replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

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
                # Send the reminder; choose behavior based on reminder_type
                if reminder_type == "morning_of":
                    # send_morning_of_notification returns number of recipients
                    recipients = send_morning_of_notification(event)
                    AutomaticReminderLog.objects.create(
                        event=event,
                        reminder_type=reminder_type,
                        recipients_count=recipients or 0,
                        success=True,
                    )
                else:
                    # Count recipients before sending (players who haven't responded)
                    recipients = get_reminder_recipients_count(event, reminder_type)
                    send_event_reminder_notification(event, days_before=days_before)
                    AutomaticReminderLog.objects.create(
                        event=event,
                        reminder_type=reminder_type,
                        recipients_count=recipients or 0,
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


def get_reminder_recipients_count(event, reminder_type: str = "1_day") -> int:
    """
    Get the count of recipients who would receive a reminder for this event.
    This mimics the logic in send_event_reminder_notification.
    """
    try:
        from attendance.models import Attendance
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # For morning_of reminders we only count players who are marked as present
        if reminder_type == "morning_of":
            attending_qs = Attendance.objects.filter(
                event=event, present=True
            ).select_related("user")
            return sum(1 for att in attending_qs if getattr(att.user, "email", None))

        # For other reminders count active players who haven't submitted attendance yet
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


@shared_task(bind=True, max_retries=2)
def send_event_summary_to_attendees(self, reminder_type: str = "morning_of"):
    """
    Send morning-of notifications for events happening today to players who are marked as attending.
    This task finds events with a date on the current day and sends an email listing attending players.
    """

    days_mapping = {
        "1_week": 7,
        "3_days": 3,
        "1_day": 1,
        "morning_of": 0,  # Morning of event doesn't use days before
    }

    days_before = days_mapping.get(reminder_type, 0)

    # Calculate target date (events that are exactly X days from now)
    now = timezone.now()
    target_date_start = (now + timedelta(days=days_before)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    target_date_end = target_date_start.replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    logger.info(
        f"Searching for events occurring today between {target_date_start} and {target_date_end}"
    )

    events_today = Event.objects.filter(
        date__gte=target_date_start, date__lte=target_date_end
    )

    total_events = events_today.count()
    successful = 0
    failed = 0

    for event in events_today:
        try:
            recipients = send_morning_of_notification(event)

            # Log success to AutomaticReminderLog (reuse model for notification logging)
            try:
                AutomaticReminderLog.objects.update_or_create(
                    event=event,
                    reminder_type="morning_of",
                    defaults={
                        "recipients_count": recipients or 0,
                        "success": True,
                    },
                )
            except Exception as log_err:
                logger.error(
                    f"Failed to log morning-of notification for event {event.pk}: {log_err}"
                )

            successful += 1
            logger.info(f"Morning-of notification processed for event {event.name}")

        except Exception as e:
            failed += 1
            try:
                AutomaticReminderLog.objects.update_or_create(
                    event=event,
                    reminder_type="morning_of",
                    defaults={
                        "recipients_count": 0,
                        "success": False,
                        "error_message": str(e),
                    },
                )
            except Exception as log_err:
                logger.error(
                    f"Failed to log morning-of notification failure for event {event.pk}: {log_err}"
                )

            logger.error(
                f"Failed to send morning-of notification for event {event.name}: {e}"
            )

    result = {
        "total_events": total_events,
        "successful": successful,
        "failed": failed,
    }

    logger.info(
        f"Morning-of notifications complete: {successful} successful, {failed} failed out of {total_events}"
    )

    if failed > 0 and self.request.retries < self.max_retries:
        logger.info(
            f"Retrying morning-of notifications (attempt {self.request.retries + 1})"
        )
        raise self.retry(countdown=300)

    return result
