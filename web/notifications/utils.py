"""
Notification utilities for the SV Rap 8 application.
"""

import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

logger = logging.getLogger(__name__)

User = get_user_model()


def sync_periodic_tasks():
    """
    Synchronize ScheduleConfiguration and EventScheduleOverride models
    with django-celery-beat PeriodicTask models.
    """
    from .models import EventScheduleOverride, ScheduleConfiguration

    # Get all active schedule configurations
    configs = ScheduleConfiguration.objects.filter(enabled=True)

    for config in configs:
        # Create or update the periodic task for this configuration
        task_name = f"auto_{config.name.lower().replace(' ', '_')}"

        # Create or get the crontab schedule
        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=config.minute,
            hour=config.hour,
            day_of_week=config.day_of_week,
            day_of_month=config.day_of_month,
            month_of_year=config.month_of_year,
            defaults={"timezone": "Europe/Amsterdam"},
        )

        # Prepare task kwargs
        task_kwargs = {}
        if config.reminder_type:
            task_kwargs["reminder_type"] = config.reminder_type

        # Create or update periodic task
        periodic_task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                "task": config.task,
                "crontab": crontab_schedule,
                "kwargs": json.dumps(task_kwargs) if task_kwargs else "{}",
                "enabled": True,
                "description": f"Auto-generated from ScheduleConfiguration: {config.name}",
            },
        )

        logger.info(f"{'Created' if created else 'Updated'} periodic task: {task_name}")

    # Handle event-specific overrides
    overrides = EventScheduleOverride.objects.filter(enabled=True)

    for override in overrides:
        event = override.event
        config = override.configuration

        # Create task name specific to this event
        task_name = f"event_{event.id}_{config.name.lower().replace(' ', '_')}"

        # Get effective schedule (overrides applied)
        effective_schedule = override.get_effective_schedule()

        # Create or get the crontab schedule for this override
        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=effective_schedule["minute"],
            hour=effective_schedule["hour"],
            day_of_week=effective_schedule["day_of_week"],
            day_of_month=effective_schedule["day_of_month"],
            month_of_year=effective_schedule["month_of_year"],
            defaults={"timezone": "Europe/Amsterdam"},
        )

        # Prepare task kwargs
        task_kwargs = {}
        if config.reminder_type:
            task_kwargs["reminder_type"] = config.reminder_type
        # Add event-specific context
        task_kwargs["event_id"] = event.id

        # Create or update periodic task for this event override
        periodic_task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                "task": config.task,
                "crontab": crontab_schedule,
                "kwargs": json.dumps(task_kwargs),
                "enabled": True,
                "description": f"Auto-generated override for event: {event.name}",
            },
        )

        logger.info(
            f"{'Created' if created else 'Updated'} event override task: {task_name}"
        )

    # Clean up orphaned auto-generated tasks
    cleanup_orphaned_tasks()

    logger.info("Periodic task synchronization completed")


def cleanup_orphaned_tasks():
    """
    Remove auto-generated periodic tasks that no longer have corresponding configurations.
    """
    from .models import EventScheduleOverride, ScheduleConfiguration

    # Get all auto-generated task names that should exist
    expected_task_names = set()

    # Add general config task names
    for config in ScheduleConfiguration.objects.filter(enabled=True):
        task_name = f"auto_{config.name.lower().replace(' ', '_')}"
        expected_task_names.add(task_name)

    # Add event override task names
    for override in EventScheduleOverride.objects.filter(enabled=True):
        event = override.event
        config = override.configuration
        task_name = f"event_{event.id}_{config.name.lower().replace(' ', '_')}"
        expected_task_names.add(task_name)

    # Find and delete orphaned auto-generated tasks
    orphaned_tasks = PeriodicTask.objects.filter(name__startswith="auto_").exclude(
        name__in=expected_task_names
    )

    orphaned_event_tasks = PeriodicTask.objects.filter(
        name__startswith="event_"
    ).exclude(name__in=expected_task_names)

    # Delete orphaned tasks
    for task in orphaned_tasks:
        logger.info(f"Deleting orphaned auto-generated task: {task.name}")
        task.delete()

    for task in orphaned_event_tasks:
        logger.info(f"Deleting orphaned event override task: {task.name}")
        task.delete()


def send_new_event_notification(event):
    """
    Send email notification to all active players when a new event is created.

    Args:
        event: The Event instance that was just created
    """
    # Get all active players with email addresses
    active_players = User.objects.filter(is_active=True, email__isnull=False).exclude(
        email=""
    )

    if not active_players.exists():
        logger.info(
            "No active players with email addresses found for event notification"
        )
        return

    # Get recipient email list
    recipient_list = [player.email for player in active_players if player.email]

    if not recipient_list:
        logger.info("No valid email addresses found for event notification")
        return

    # Prepare email context
    # Convert to local timezone before formatting
    local_date = timezone.localtime(event.date)
    context = {
        "event": event,
        "event_date_formatted": local_date.strftime("%d-%m-%Y om %H:%M"),
        "event_type_display": event.get_event_type_display(),
        "is_mandatory_text": "Ja" if event.is_mandatory else "Nee",
        "site_name": "SV Rap 8",
        "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        "events_url": f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/events/",
    }

    # Render email content
    subject = f"Nieuw evenement: {event.name}"

    # Create both HTML and plain text versions
    html_message = render_to_string("notifications/emails/new_event.html", context)
    plain_message = render_to_string("notifications/emails/new_event.txt", context)

    try:
        # Send email to all active players
        from_email = (
            getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@localhost"
        )
        if not getattr(settings, "DEFAULT_FROM_EMAIL", None):
            logger.warning(
                "DEFAULT_FROM_EMAIL not set; using fallback 'noreply@localhost'"
            )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"New event notification sent for '{event.name}' to {len(recipient_list)} recipients"
        )

    except Exception as e:
        logger.error(
            f"Failed to send new event notification for '{event.name}': {str(e)}"
        )
        raise


def send_event_reminder_notification(event, days_before: int = 1):
    """
    Send reminder email notification for an upcoming event.

    Args:
        event: The Event instance to send reminder for
        days_before: Number of days before the event (for logging purposes)
    """
    # Get all active players with email addresses who haven't responded yet
    from attendance.models import Attendance

    # Get players who haven't submitted their attendance yet
    responded_user_ids = Attendance.objects.filter(event=event).values_list(
        "user_id", flat=True
    )

    active_players = (
        User.objects.filter(is_active=True, email__isnull=False)
        .exclude(email="")
        .exclude(id__in=responded_user_ids)
    )

    if not active_players.exists():
        logger.info(f"No players need reminders for event '{event.name}'")
        return

    # Get recipient email list
    recipient_list = [player.email for player in active_players if player.email]

    if not recipient_list:
        logger.info(f"No valid email addresses found for event reminder '{event.name}'")
        return

    # Prepare email context
    # Convert to local timezone before formatting
    local_date = timezone.localtime(event.date)
    context = {
        "event": event,
        "event_date_formatted": local_date.strftime("%d-%m-%Y om %H:%M"),
        "event_type_display": event.get_event_type_display(),
        "is_mandatory_text": "Ja" if event.is_mandatory else "Nee",
        "days_before": days_before,
        "site_name": "SV Rap 8",
        "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        "events_url": f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/events/",
    }

    # Render email content
    subject = f"Herinnering: {event.name} - Geef je aanwezigheid door"

    # Create both HTML and plain text versions
    html_message = render_to_string("notifications/emails/event_reminder.html", context)
    plain_message = render_to_string("notifications/emails/event_reminder.txt", context)

    try:
        # Send email to players who haven't responded
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Event reminder sent for '{event.name}' to {len(recipient_list)} recipients"
        )

    except Exception as e:
        logger.error(f"Failed to send event reminder for '{event.name}': {str(e)}")
        raise


def send_recurring_event_notification(events: list):
    """
    Send a single email notification for a series of recurring events.

    Args:
        events: List of Event instances that are part of the same recurring series
    """
    if not events:
        logger.info("No events provided for recurring event notification")
        return

    # Get all active players with email addresses
    active_players = User.objects.filter(is_active=True, email__isnull=False).exclude(
        email=""
    )

    if not active_players.exists():
        logger.info(
            "No active players with email addresses found for recurring event notification"
        )
        return

    # Get recipient email list
    recipient_list = [player.email for player in active_players if player.email]

    if not recipient_list:
        logger.info("No valid email addresses found for recurring event notification")
        return

    # Sort events by date
    events_sorted = sorted(events, key=lambda e: e.date)
    first_event = events_sorted[0]
    last_event = events_sorted[-1]

    # Prepare email context
    # Convert to local timezone before formatting
    first_event_local = timezone.localtime(first_event.date)
    last_event_local = timezone.localtime(last_event.date) if len(events_sorted) > 1 else None
    
    context = {
        "event": first_event,  # Use first event as the base
        "first_event_date_formatted": first_event_local.strftime("%d-%m-%Y om %H:%M"),
        "last_event_date_formatted": (
            last_event_local.strftime("%d-%m-%Y om %H:%M")
            if last_event_local
            else None
        ),
        "event_type_display": first_event.get_event_type_display(),
        "is_mandatory_text": "Ja" if first_event.is_mandatory else "Nee",
        "recurrence_display": first_event.get_recurrence_display(),
        "total_events": len(events),
        "site_name": "SV Rap 8",
        "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        "events_url": f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/events/",
    }

    # Render email content
    subject = f"Herhalend evenement: {first_event.name}"

    # Create both HTML and plain text versions
    html_message = render_to_string(
        "notifications/emails/recurring_event.html", context
    )
    plain_message = render_to_string(
        "notifications/emails/recurring_event.txt", context
    )

    try:
        # Send email to all active players
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Recurring event notification sent for '{first_event.name}' "
            f"({len(events)} events) to {len(recipient_list)} recipients"
        )

    except Exception as e:
        logger.error(
            f"Failed to send recurring event notification for '{first_event.name}': {str(e)}"
        )
        raise


def send_bulk_notifications(events: list, notification_type: str = "new_event"):
    """
    Send notifications for multiple events.
    For recurring events, sends one consolidated email.
    For individual events, sends separate emails.

    Args:
        events: List of Event instances
        notification_type: Type of notification ('new_event', 'reminder', 'recurring_event')
    """
    if not events:
        logger.info("No events provided for bulk notifications")
        return 0, 0

    success_count = 0
    error_count = 0

    # Check if these are recurring events (all have the same recurring_event_link_id)
    first_event = events[0]
    is_recurring_series = first_event.is_recurring and all(
        event.recurring_event_link_id == first_event.recurring_event_link_id
        for event in events
    )

    if is_recurring_series and notification_type == "new_event":
        # Send one consolidated email for the recurring series
        try:
            send_recurring_event_notification(events)
            success_count = 1  # Count as one successful notification
        except Exception as e:
            logger.error(f"Failed to send recurring event notification: {str(e)}")
            error_count = 1
    else:
        # Send individual notifications for each event
        for event in events:
            try:
                if notification_type == "new_event":
                    send_new_event_notification(event)
                elif notification_type == "reminder":
                    send_event_reminder_notification(event)
                success_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to send {notification_type} notification for event {event.id}: {str(e)}"
                )
                error_count += 1

    logger.info(
        f"Bulk notifications complete: {success_count} successful, {error_count} failed"
    )

    return success_count, error_count


def send_morning_of_notification(event):
    """
    Send a morning-of email to all players who are marked as attending for the given event.

    The email contains event details and a list of attending players.
    """
    try:
        from attendance.models import Attendance

        # Get attendances where the boolean `present` indicates attending
        attending_qs = Attendance.objects.filter(
            event=event, present=True
        ).select_related("user")

        if not attending_qs.exists():
            logger.info(
                f"No attending players found for morning-of notification for event '{event.name}'"
            )
            return 0

        # Build recipient list and attendees display list
        recipient_list = []
        attendees = []
        for att in attending_qs:
            user = att.user
            if getattr(user, "email", None):
                recipient_list.append(user.email)
            display_name = getattr(user, "get_full_name", None)
            if callable(display_name):
                name = user.get_full_name() or user.username
            else:
                name = getattr(user, "username", str(user))
            attendees.append(name)

        if not recipient_list:
            logger.info(
                f"No valid email addresses for attending players for event '{event.name}'"
            )
            return 0

        # Prepare context
        # Convert to local timezone before formatting
        local_date = timezone.localtime(event.date)
        context = {
            "event": event,
            "event_date_formatted": local_date.strftime("%d-%m-%Y om %H:%M"),
            "event_type_display": event.get_event_type_display(),
            "is_mandatory_text": "Ja" if event.is_mandatory else "Nee",
            "attendees": attendees,
            "site_name": "SV Rap 8",
            "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        }

        subject = f"Vandaag: {event.name} - Aanwezige spelers"

        html_message = render_to_string(
            "notifications/emails/morning_of_event.html", context
        )
        plain_message = render_to_string(
            "notifications/emails/morning_of_event.txt", context
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Morning-of notification sent for '{event.name}' to {len(recipient_list)} recipients"
        )
    except Exception as e:
        logger.error(f"Failed to send morning-of notification for '{event.name}': {e}")
        raise

    return len(recipient_list)
