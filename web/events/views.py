import json

from attendance.models import Attendance
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Prefetch
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EventForm
from .models import Event

User = get_user_model()


def event_list(request: HttpRequest):
    now = timezone.now()

    # Get filter parameters
    search_query = request.GET.get("search", "").strip()
    event_type_filter = request.GET.get("type", "")
    location_filter = request.GET.get("location", "")
    mandatory_filter = request.GET.get("mandatory", "")

    # Base querysets
    upcoming_events = Event.objects.filter(date__gt=now)
    past_events = Event.objects.filter(date__lte=now)

    # Apply search filter
    if search_query:
        from django.db.models import Q

        search_filter = (
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(location__icontains=search_query)
        )
        upcoming_events = upcoming_events.filter(search_filter)
        past_events = past_events.filter(search_filter)

    # Apply event type filter
    if event_type_filter:
        upcoming_events = upcoming_events.filter(event_type=event_type_filter)
        past_events = past_events.filter(event_type=event_type_filter)

    # Apply location filter
    if location_filter:
        upcoming_events = upcoming_events.filter(location__icontains=location_filter)
        past_events = past_events.filter(location__icontains=location_filter)

    # Apply mandatory filter
    if mandatory_filter:
        is_mandatory = mandatory_filter == "true"
        upcoming_events = upcoming_events.filter(is_mandatory=is_mandatory)
        past_events = past_events.filter(is_mandatory=is_mandatory)

    # Order the results
    upcoming_events = upcoming_events.order_by("date")
    past_events = past_events.order_by("-date")

    # If user is authenticated, prefetch their attendance for each event
    if request.user.is_authenticated:
        user_attendance_prefetch = Prefetch(
            "attendance_set",
            queryset=Attendance.objects.filter(user=request.user),
            to_attr="user_attendance",
        )
        upcoming_events = upcoming_events.prefetch_related(user_attendance_prefetch)
        past_events = past_events.prefetch_related(user_attendance_prefetch)

    # Get unique locations for filter dropdown
    unique_locations = (
        Event.objects.exclude(location__exact="")
        .values_list("location", flat=True)
        .distinct()
        .order_by("location")
    )

    context = {
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "now": now,
        "search_query": search_query,
        "event_type_filter": event_type_filter,
        "location_filter": location_filter,
        "mandatory_filter": mandatory_filter,
        "event_types": Event.EVENT_TYPES,
        "unique_locations": unique_locations,
    }

    return render(request, "events/event_list.html", context)


def event_create(request: HttpRequest):
    if not request.user.is_staff:
        return redirect("events:list")
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Evenement succesvol aangemaakt.")
            return redirect("events:list")
    else:
        form = EventForm()
    return render(request, "events/event_form.html", {"form": form})


def event_edit(request: HttpRequest, pk: int):
    if not request.user.is_staff:
        return redirect("events:list")
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Evenement succesvol bijgewerkt.")
            return redirect("events:list")
    else:
        form = EventForm(instance=event)
    return render(request, "events/event_form.html", {"form": form, "event": event})


def is_staff(user):
    """Check if user is staff"""
    return user.is_staff


@user_passes_test(is_staff)
def admin_attendance(request: HttpRequest, pk: int):
    """Admin view to manage attendance for all players for a specific event"""
    event = get_object_or_404(Event, pk=pk)

    # Get all active players
    players = User.objects.filter(is_active=True).order_by("last_name", "first_name")

    # Get existing attendance records
    attendances = {
        att.user_id: att
        for att in Attendance.objects.filter(event=event).select_related("user")
    }

    # Create player attendance data
    player_attendance = []
    for player in players:
        attendance = attendances.get(player.id)
        player_attendance.append(
            {
                "player": player,
                "attendance": attendance,
                "present": attendance.present if attendance else None,
            }
        )

    # Handle bulk update
    if request.method == "POST":
        updated_count = 0
        for player in players:
            present_value = request.POST.get(f"attendance_{player.id}")
            if present_value is not None:
                present = present_value == "present"
                attendance, created = Attendance.objects.get_or_create(
                    user=player, event=event, defaults={"present": present}
                )
                if not created and attendance.present != present:
                    attendance.present = present
                    attendance.save()
                    updated_count += 1
                elif created:
                    updated_count += 1

        messages.success(
            request, f"Aanwezigheid bijgewerkt voor {updated_count} spelers."
        )
        return redirect("events:admin_attendance", pk=event.pk)

    context = {
        "event": event,
        "player_attendance": player_attendance,
        "total_players": len(player_attendance),
        "present_count": sum(1 for pa in player_attendance if pa["present"] is True),
        "absent_count": sum(1 for pa in player_attendance if pa["present"] is False),
        "no_response_count": sum(
            1 for pa in player_attendance if pa["present"] is None
        ),
    }

    return render(request, "events/admin_attendance.html", context)


@user_passes_test(is_staff)
@require_POST
def admin_bulk_attendance(request: HttpRequest, pk: int):
    """AJAX endpoint for bulk attendance updates"""
    event = get_object_or_404(Event, pk=pk)

    try:
        data = json.loads(request.body)
        action = data.get("action")

        if action == "mark_all_present":
            # Mark all active players as present
            players = User.objects.filter(is_active=True)
            updated_count = 0
            for player in players:
                attendance, created = Attendance.objects.get_or_create(
                    user=player, event=event, defaults={"present": True}
                )
                if not created and not attendance.present:
                    attendance.present = True
                    attendance.save()
                    updated_count += 1
                elif created:
                    updated_count += 1

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Alle {updated_count} spelers gemarkeerd als aanwezig.",
                    "updated_count": updated_count,
                }
            )

        elif action == "mark_all_absent":
            # Mark all active players as absent
            players = User.objects.filter(is_active=True)
            updated_count = 0
            for player in players:
                attendance, created = Attendance.objects.get_or_create(
                    user=player, event=event, defaults={"present": False}
                )
                if not created and attendance.present:
                    attendance.present = False
                    attendance.save()
                    updated_count += 1
                elif created:
                    updated_count += 1

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Alle {updated_count} spelers gemarkeerd als afwezig.",
                    "updated_count": updated_count,
                }
            )

        elif action == "clear_all":
            # Clear all attendance records
            deleted_count = Attendance.objects.filter(event=event).count()
            Attendance.objects.filter(event=event).delete()

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Aanwezigheid gewist voor {deleted_count} spelers.",
                    "deleted_count": deleted_count,
                }
            )

        else:
            return JsonResponse({"success": False, "error": "Onbekende actie"})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Ongeldige JSON data"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
