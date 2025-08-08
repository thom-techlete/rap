from django import template
from django.contrib.auth.models import User  # Add import for user type

from events.models import Event  # Add import for type annotation

register = template.Library()


@register.filter
def user_attendance_status(event: Event, user: User):
    """
    Template filter to get the attendance status of a user for an event.
    Returns: True (present), False (absent), None (no response)
    """
    if not user.is_authenticated:
        return None

    try:
        # Import here to avoid circular imports
        from attendance.models import Attendance

        attendance = Attendance.objects.get(user=user, event=event)
        return attendance.present
    except Exception:
        return None


@register.filter
def attendance_count(event: Event):
    """
    Template filter to get the total number of attendees for an event.
    """
    try:
        return event.get_attendance_count()
    except Exception:
        return 0


@register.filter
def attendance_status_text(status: bool | None):
    """
    Template filter to get human-readable text for attendance status.
    """
    if status is True:
        return "Aanwezig"
    elif status is False:
        return "Afwezig"
    else:
        return "Geen reactie"


@register.filter
def attendance_status_class(status: bool | None):
    """
    Template filter to get CSS class for attendance status.
    """
    if status is True:
        return "success"
    elif status is False:
        return "danger"
    else:
        return "secondary"
