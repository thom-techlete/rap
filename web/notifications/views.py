from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from events.models import Event

from .utils import send_event_reminder_notification, send_new_event_notification


def is_staff(user):
    """Check if user is staff"""
    return user.is_staff


@user_passes_test(is_staff)
@require_POST
def send_event_notification(request, event_id):
    """Send new event notification manually"""
    event = get_object_or_404(Event, id=event_id)

    try:
        send_new_event_notification(event)
        messages.success(
            request,
            f"Nieuwe evenement notificatie succesvol verzonden voor '{event.name}'",
        )
    except Exception as e:
        messages.error(
            request, f"Fout bij verzenden notificatie voor '{event.name}': {str(e)}"
        )

    return redirect("events:list")


@user_passes_test(is_staff)
@require_POST
def send_event_reminder(request, event_id):
    """Send event reminder notification manually"""
    event = get_object_or_404(Event, id=event_id)

    try:
        send_event_reminder_notification(event)
        messages.success(
            request, f"Herinnering succesvol verzonden voor '{event.name}'"
        )
    except Exception as e:
        messages.error(
            request, f"Fout bij verzenden herinnering voor '{event.name}': {str(e)}"
        )

    return redirect("events:list")


@user_passes_test(is_staff)
def notification_status(request):
    """AJAX endpoint to check notification sending status"""
    # This could be extended to show notification logs/status
    return JsonResponse(
        {"status": "active", "message": "Notification system is operational"}
    )
