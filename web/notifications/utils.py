"""
Notification utilities for the SV Rap 8 application.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

User = get_user_model()


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
    context = {
        "event": event,
        "event_date_formatted": event.date.strftime("%d-%m-%Y om %H:%M"),
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
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
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
    context = {
        "event": event,
        "event_date_formatted": event.date.strftime("%d-%m-%Y om %H:%M"),
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
    context = {
        "event": first_event,  # Use first event as the base
        "first_event_date_formatted": first_event.date.strftime("%d-%m-%Y om %H:%M"),
        "last_event_date_formatted": (
            last_event.date.strftime("%d-%m-%Y om %H:%M")
            if len(events_sorted) > 1
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
