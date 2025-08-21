"""
Celery tasks for automatic notifications.
"""

import logging
from datetime import timedelta
import json
import requests
from typing import Dict, List, Optional

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from events.models import Event

from notifications.models import AutomaticReminderLog, PushSubscription, PushNotificationLog
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


# ==============================================================================
# PUSH NOTIFICATION TASKS
# ==============================================================================

@shared_task(bind=True, max_retries=3)
def send_push_notification(self, subscription_id: int, notification_data: Dict) -> bool:
    """
    Send a push notification to a specific subscription.
    
    Args:
        subscription_id: ID of the PushSubscription
        notification_data: Dict containing title, body, url, icon etc.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from pywebpush import webpush, WebPushException
        
        subscription = PushSubscription.objects.get(id=subscription_id)
        
        # Create notification log entry
        log_entry = PushNotificationLog.objects.create(
            subscription=subscription,
            title=notification_data.get('title', 'SV Rap 8'),
            body=notification_data.get('body', ''),
            url=notification_data.get('url', ''),
            icon=notification_data.get('icon', ''),
        )
        
        # Prepare subscription info for pywebpush
        subscription_info = subscription.get_subscription_info()
        
        # VAPID claims
        vapid_claims = {
            "sub": f"mailto:{getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')}"
        }
        
        # Send push notification
        response = webpush(
            subscription_info=subscription_info,
            data=json.dumps(notification_data),
            vapid_private_key=getattr(settings, 'VAPID_PRIVATE_KEY', None),
            vapid_claims=vapid_claims
        )
        
        # Update log with success
        log_entry.success = True
        log_entry.response_code = response.status_code if hasattr(response, 'status_code') else 200
        log_entry.save()
        
        logger.info(f"Push notification sent successfully to {subscription.user.get_full_name()}")
        return True
        
    except PushSubscription.DoesNotExist:
        logger.error(f"Push subscription {subscription_id} not found")
        return False
        
    except Exception as e:
        # Update log with error
        if 'log_entry' in locals():
            log_entry.error_message = str(e)
            log_entry.response_code = getattr(e, 'response', {}).get('status_code', 0)
            log_entry.save()
        
        logger.error(f"Failed to send push notification: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return False


@shared_task
def send_push_to_users(user_ids: List[int], notification_data: Dict) -> Dict:
    """
    Send push notifications to multiple users.
    
    Args:
        user_ids: List of user IDs to send notifications to
        notification_data: Dict containing notification content
    
    Returns:
        Dict with success/failure counts
    """
    results = {'sent': 0, 'failed': 0, 'no_subscription': 0}
    
    # Get active subscriptions for the users
    subscriptions = PushSubscription.objects.filter(
        user_id__in=user_ids,
        is_active=True
    ).select_related('user')
    
    for subscription in subscriptions:
        # Send notification asynchronously
        success = send_push_notification.delay(subscription.id, notification_data)
        if success:
            results['sent'] += 1
        else:
            results['failed'] += 1
    
    # Track users without subscriptions
    users_with_subs = set(sub.user_id for sub in subscriptions)
    users_without_subs = set(user_ids) - users_with_subs
    results['no_subscription'] = len(users_without_subs)
    
    logger.info(f"Push notification batch: {results}")
    return results


@shared_task
def send_event_push_notification(event_id: int, message_type: str = 'reminder') -> Dict:
    """
    Send push notifications for event-related updates.
    
    Args:
        event_id: ID of the event
        message_type: Type of message ('reminder', 'new_event', 'update', 'cancelled')
    
    Returns:
        Dict with sending results
    """
    try:
        event = Event.objects.get(id=event_id)
        
        # Get all active users who should receive notifications
        from users.models import Player
        users = Player.objects.filter(is_active=True, email_verified=True)
        user_ids = list(users.values_list('id', flat=True))
        
        # Prepare notification content based on message type
        if message_type == 'reminder':
            title = f'Herinnering: {event.name}'
            body = f'Evenement op {event.date.strftime("%d/%m/%Y om %H:%M")}'
            icon = '/static/media/icons/icon-192x192.png'
            
        elif message_type == 'new_event':
            title = 'Nieuw evenement aangemaakt'
            body = f'{event.name} op {event.date.strftime("%d/%m/%Y om %H:%M")}'
            icon = '/static/media/icons/icon-192x192.png'
            
        elif message_type == 'update':
            title = f'Evenement bijgewerkt: {event.name}'
            body = f'Wijzigingen voor evenement op {event.date.strftime("%d/%m/%Y")}'
            icon = '/static/media/icons/icon-192x192.png'
            
        elif message_type == 'cancelled':
            title = f'Evenement geannuleerd: {event.name}'
            body = f'Het evenement van {event.date.strftime("%d/%m/%Y")} is geannuleerd'
            icon = '/static/media/icons/icon-192x192.png'
            
        else:
            title = f'SV Rap 8: {event.name}'
            body = f'Update voor evenement op {event.date.strftime("%d/%m/%Y")}'
            icon = '/static/media/icons/icon-192x192.png'
        
        notification_data = {
            'title': title,
            'body': body,
            'icon': icon,
            'badge': '/static/media/icons/icon-96x96.png',
            'url': f'/events/{event.id}/',
            'tag': f'event-{event.id}-{message_type}',
            'requireInteraction': message_type in ['new_event', 'cancelled'],
            'actions': [
                {
                    'action': 'open',
                    'title': 'Bekijk evenement',
                    'icon': '/static/media/icons/icon-96x96.png'
                },
                {
                    'action': 'close',
                    'title': 'Sluiten'
                }
            ],
            'data': {
                'url': f'/events/{event.id}/',
                'event_id': event.id,
                'message_type': message_type
            }
        }
        
        # Send to all users
        results = send_push_to_users.delay(user_ids, notification_data)
        
        logger.info(f"Event push notification sent for {event.name}: {results}")
        return results
        
    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found for push notification")
        return {'error': 'Event not found'}
    
    except Exception as e:
        logger.error(f"Failed to send event push notification: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_invalid_push_subscriptions():
    """
    Clean up push subscriptions that are no longer valid.
    This task should be run periodically to remove expired or invalid subscriptions.
    """
    deleted_count = 0
    
    # Find subscriptions that haven't been used in 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    old_subscriptions = PushSubscription.objects.filter(
        last_used__lt=cutoff_date,
        is_active=True
    )
    
    for subscription in old_subscriptions:
        # Try to send a test notification to check if subscription is still valid
        test_data = {
            'title': 'Test',
            'body': 'Testing subscription validity',
            'tag': 'test-subscription'
        }
        
        # If sending fails, mark as inactive
        success = send_push_notification.delay(subscription.id, test_data)
        if not success:
            subscription.is_active = False
            subscription.save()
            deleted_count += 1
    
    logger.info(f"Cleaned up {deleted_count} invalid push subscriptions")
    return deleted_count
