import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from events.models import Event

from .models import Attendance

User = get_user_model()


@login_required
def mark_attendance(request: HttpRequest, event_id: int):
    event = get_object_or_404(Event, id=event_id)
    attendance, _ = Attendance.objects.get_or_create(user=request.user, event=event)

    if request.method == "POST":
        attendance.present = not attendance.present
        attendance.save()

        status = "aanwezig" if attendance.present else "afwezig"
        messages.success(request, f"Je bent gemarkeerd als {status} voor {event.name}.")
        return redirect("events:list")

    return render(
        request,
        "attendance/mark_attendance.html",
        {"event": event, "attendance": attendance},
    )


@login_required
def dashboard(request: HttpRequest):
    """Dashboard showing attendance overview for the user"""
    from django.utils import timezone

    # Only consider past events for statistics
    now = timezone.now()
    past_events = Event.objects.filter(date__lt=now).order_by("-date")

    # Get user's attendance records for past events only
    user_attendances = (
        Attendance.objects.filter(user=request.user, event__in=past_events)
        .select_related("event")
        .order_by("-event__date")
    )

    # Create a comprehensive attendance history including events without responses
    attendance_dict = {att.event.id: att for att in user_attendances}

    # Build complete attendance history (last 10 past events)
    recent_attendance_history = []
    for event in past_events[:10]:
        attendance_record = attendance_dict.get(event.id)
        if attendance_record:
            # User has an explicit attendance record
            recent_attendance_history.append(
                {
                    "event": event,
                    "attendance": attendance_record,
                    "present": attendance_record.present,
                    "timestamp": attendance_record.timestamp,
                    "has_response": True,
                }
            )
        else:
            # No attendance record = automatically absent for past events
            recent_attendance_history.append(
                {
                    "event": event,
                    "attendance": None,
                    "present": False,
                    "timestamp": None,
                    "has_response": False,
                }
            )

    # Calculate stats based on past events only
    total_past_events = past_events.count()
    present_count = user_attendances.filter(present=True).count()

    # Attendance rate calculation:
    # - If no past events, rate is 0
    # - If past events exist, rate = (present count) / (total past events) * 100
    # - Missing attendance records are treated as absent
    attendance_rate = (
        (present_count / total_past_events * 100) if total_past_events > 0 else 0
    )
    absent_count = total_past_events - present_count

    # Calculate progress to goal
    target_rate = 80
    remaining_to_goal = max(0, target_rate - attendance_rate)

    context: dict[str, object] = {
        "attendances": recent_attendance_history,  # Complete attendance history including missing responses
        "total_events": total_past_events,  # Only past events count for stats
        "present_count": present_count,
        "absent_count": absent_count,
        "attendance_rate": round(attendance_rate, 1),
        "remaining_to_goal": round(remaining_to_goal, 1),
        "target_rate": target_rate,
    }

    return render(request, "attendance/dashboard.html", context)


@login_required
@require_POST
def toggle_attendance(request: HttpRequest, event_id: int):
    """AJAX endpoint to toggle attendance status"""
    event = get_object_or_404(Event, id=event_id)
    attendance, _ = Attendance.objects.get_or_create(user=request.user, event=event)
    attendance.present = not attendance.present
    attendance.save()

    # Get total attendance count for this event
    attendance_count = Attendance.objects.filter(event=event, present=True).count()

    return JsonResponse(
        {
            "success": True,
            "present": attendance.present,
            "attendance_count": attendance_count,
            "message": f'Je bent gemarkeerd als {"aanwezig" if attendance.present else "afwezig"} voor {event.name}.',
        }
    )


@login_required
@require_POST
@ensure_csrf_cookie
def set_attendance(request: HttpRequest, event_id: int):
    """AJAX endpoint to set specific attendance status"""

    event = get_object_or_404(Event, id=event_id)
    data = json.loads(request.body)
    present = data.get("present")

    if present is None:
        return JsonResponse(
            {"success": False, "error": "Missing present parameter"}, status=400
        )

    attendance, _ = Attendance.objects.get_or_create(user=request.user, event=event)
    attendance.present = present
    attendance.save()

    # Get total attendance count for this event
    attendance_count = Attendance.objects.filter(event=event, present=True).count()

    return JsonResponse(
        {
            "success": True,
            "present": attendance.present,
            "attendance_count": attendance_count,
            "message": f'Je bent gemarkeerd als {"aanwezig" if attendance.present else "afwezig"} voor {event.name}.',
        }
    )
