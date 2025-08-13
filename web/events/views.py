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
from notifications.utils import send_bulk_notifications, send_new_event_notification

from .forms import EventForm, MatchStatisticForm
from .models import Event, MatchStatistic

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


def event_detail(request: HttpRequest, pk: int):
    """Show detailed view of a specific event"""
    event = get_object_or_404(Event, pk=pk)
    
    # Get all active players for attendance table
    players = User.objects.filter(is_active=True).order_by("last_name", "first_name")
    
    # Get existing attendance records
    attendances = {
        att.user_id: att
        for att in Attendance.objects.filter(event=event).select_related("user")
    }
    
    # Create player attendance data for the table
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
    
    # Get user's attendance status if authenticated
    user_attendance_status = None
    if request.user.is_authenticated:
        user_attendance_status = event.get_user_attendance_status(request.user)
    
    # Handle statistics for match events
    statistics = []
    statistic_form = None
    if event.is_match:
        # Get existing statistics for this match
        statistics = MatchStatistic.objects.filter(event=event).select_related("player").order_by("minute", "statistic_type")
        
        # Handle statistics form submission (staff only)
        if request.user.is_staff:
            if request.method == "POST" and "add_statistic" in request.POST:
                statistic_form = MatchStatisticForm(request.POST, event=event)
                if statistic_form.is_valid():
                    statistic = statistic_form.save(commit=False)
                    statistic.event = event
                    statistic.created_by = request.user
                    statistic.save()
                    messages.success(request, f"Statistiek toegevoegd voor {statistic.player}.")
                    return redirect("events:detail", pk=event.pk)
            else:
                statistic_form = MatchStatisticForm(event=event)
    
    context = {
        "event": event,
        "player_attendance": player_attendance,
        "user_attendance_status": user_attendance_status,
        "is_upcoming": event.is_upcoming,
        "total_players": len(player_attendance),
        "present_count": sum(1 for pa in player_attendance if pa["present"] is True),
        "absent_count": sum(1 for pa in player_attendance if pa["present"] is False),
        "no_response_count": sum(
            1 for pa in player_attendance if pa["present"] is None
        ),
        # Statistics context
        "statistics": statistics,
        "statistic_form": statistic_form,
    }
    
    return render(request, "events/event_detail.html", context)


def event_create(request: HttpRequest):
    if not request.user.is_staff:
        return redirect("events:list")
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            # Get recurring event data
            recurrence_type = form.cleaned_data.get("recurrence_type", "none")
            recurrence_end_date = form.cleaned_data.get("recurrence_end_date")

            # Prepare base event data
            base_event_data = {
                "name": form.cleaned_data["name"],
                "description": form.cleaned_data["description"],
                "event_type": form.cleaned_data["event_type"],
                "date": form.cleaned_data["date"],
                "location": form.cleaned_data["location"],
                "max_participants": form.cleaned_data["max_participants"],
                "is_mandatory": form.cleaned_data["is_mandatory"],
            }

            if recurrence_type and recurrence_type != "none" and recurrence_end_date:
                # Create recurring events
                events = Event.create_recurring_events(
                    base_event_data, recurrence_type, recurrence_end_date
                )
                event_count = len(events)

                # Send notification for all created events
                try:
                    success_count, error_count = send_bulk_notifications(
                        events, "new_event"
                    )
                    if error_count > 0:
                        messages.warning(
                            request,
                            f"Herhalend evenement succesvol aangemaakt ({event_count} evenementen), "
                            f"maar er is een probleem opgetreden bij het verzenden van de notificatie.",
                        )
                    else:
                        messages.success(
                            request,
                            f"Herhalend evenement succesvol aangemaakt. {event_count} evenementen toegevoegd "
                            f"en één samengevatte notificatie verzonden naar alle actieve spelers.",
                        )
                except Exception as e:
                    messages.warning(
                        request,
                        f"Herhalend evenement succesvol aangemaakt ({event_count} evenementen), "
                        f"maar er is een probleem opgetreden bij het verzenden van de notificatie: {str(e)}",
                    )
            else:
                # Create single event
                event = form.save()

                # Send notification for the new event
                try:
                    send_new_event_notification(event)
                    messages.success(
                        request,
                        "Evenement succesvol aangemaakt en notificaties verzonden naar alle actieve spelers.",
                    )
                except Exception as e:
                    messages.warning(
                        request,
                        f"Evenement succesvol aangemaakt, maar er is een probleem opgetreden "
                        f"bij het verzenden van notificaties: {str(e)}",
                    )

            return redirect("events:list")
    else:
        form = EventForm()
    return render(request, "events/event_form.html", {"form": form})


def event_edit(request: HttpRequest, pk: int):
    if not request.user.is_staff:
        return redirect("events:list")
    event = get_object_or_404(Event, pk=pk)

    # Check if this is a recurring event
    is_recurring_event = event.is_recurring

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():

            if is_recurring_event:
                # Get the user's choice for updating the series
                update_series = request.POST.get("update_series", "false") == "true"

                if update_series:
                    # Update all future events in the series
                    recurring_events = event.get_recurring_events()
                    updated_count = 0

                    for recurring_event in recurring_events:
                        # Only update events that come after or are the same as the event being edited
                        if recurring_event.date >= event.date:
                            # Update with new data but preserve individual dates for other events
                            recurring_event.name = form.cleaned_data["name"]
                            recurring_event.description = form.cleaned_data[
                                "description"
                            ]
                            recurring_event.event_type = form.cleaned_data["event_type"]
                            recurring_event.location = form.cleaned_data["location"]
                            recurring_event.max_participants = form.cleaned_data[
                                "max_participants"
                            ]
                            recurring_event.is_mandatory = form.cleaned_data[
                                "is_mandatory"
                            ]

                            # For the current event being edited, also update the date
                            if recurring_event.pk == event.pk:
                                recurring_event.date = form.cleaned_data["date"]
                            else:
                                # For other events, update only the time while preserving the date
                                # Convert both dates to local timezone for proper comparison
                                new_local = timezone.localtime(
                                    form.cleaned_data["date"]
                                )
                                current_event_local = timezone.localtime(
                                    recurring_event.date
                                )

                                # Create new datetime with updated time from the form
                                updated_datetime = current_event_local.replace(
                                    hour=new_local.hour,
                                    minute=new_local.minute,
                                    second=new_local.second,
                                    microsecond=new_local.microsecond,
                                )

                                # Convert back to the same timezone as the original
                                recurring_event.date = updated_datetime

                            recurring_event.save()
                            updated_count += 1

                    messages.success(
                        request,
                        f"Herhalend evenement succesvol bijgewerkt. {updated_count} evenementen vanaf deze datum aangepast.",
                    )
                else:
                    # Update only this single event and remove it from the series
                    event.recurring_event_link_id = None
                    event.recurrence_type = "none"
                    event.recurrence_end_date = None

                    form.save()
                    messages.success(
                        request,
                        "Evenement succesvol bijgewerkt en losgemaakt van de herhalende reeks.",
                    )
            else:
                # This is not a recurring event, just update normally
                form.save()
                messages.success(request, "Evenement succesvol bijgewerkt.")

            return redirect("events:list")
    else:
        form = EventForm(instance=event)

    context = {
        "form": form,
        "event": event,
        "is_recurring_event": is_recurring_event,
    }

    if is_recurring_event:
        recurring_events = event.get_recurring_events()
        future_events = recurring_events.filter(date__gte=timezone.now())
        context["recurring_events_count"] = recurring_events.count()
        context["future_recurring_events_count"] = future_events.count()

    return render(request, "events/event_form.html", context)


def event_delete(request: HttpRequest, pk: int):
    if not request.user.is_staff:
        return redirect("events:list")

    event = get_object_or_404(Event, pk=pk)

    # Check if this is a recurring event
    is_recurring_event = event.is_recurring
    delete_series = request.POST.get("delete_series", "false") == "true"

    if request.method == "POST":
        if is_recurring_event and delete_series:
            # Delete all future events in the series
            future_events = Event.objects.filter(
                recurring_event_link_id=event.recurring_event_link_id,
                date__gte=event.date,
            )
            event_count = future_events.count()
            future_events.delete()

            messages.success(
                request,
                f"Herhalend evenement succesvol verwijderd. {event_count} evenementen verwijderd.",
            )
        else:
            # Delete only this single event
            event_name = event.name
            event.delete()

            if is_recurring_event:
                messages.success(
                    request,
                    f"Evenement '{event_name}' succesvol verwijderd uit de herhalingsserie.",
                )
            else:
                messages.success(
                    request, f"Evenement '{event_name}' succesvol verwijderd."
                )

        return redirect("events:list")

    context = {
        "event": event,
        "is_recurring_event": is_recurring_event,
    }

    if is_recurring_event:
        context["future_events_count"] = Event.objects.filter(
            recurring_event_link_id=event.recurring_event_link_id, date__gte=event.date
        ).count()

    return render(request, "events/event_delete.html", context)


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


@user_passes_test(is_staff)
@require_POST
def delete_statistic(request: HttpRequest, pk: int, stat_id: int):
    """Delete a match statistic"""
    event = get_object_or_404(Event, pk=pk)
    statistic = get_object_or_404(MatchStatistic, pk=stat_id, event=event)
    
    player_name = statistic.player.get_full_name() or statistic.player.username
    stat_type = statistic.get_statistic_type_display()
    
    statistic.delete()
    messages.success(request, f"Statistiek '{stat_type}' voor {player_name} verwijderd.")
    
    return redirect("events:detail", pk=event.pk)
