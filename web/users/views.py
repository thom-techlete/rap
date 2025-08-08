from datetime import datetime, timedelta

from attendance.models import Attendance
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from events.models import Event

from .forms import (
    CustomAuthenticationForm,
    InvitationCodeRegistrationForm,
    PlayerProfileForm,
)
from .models import InvitationCode, Player


def register(request: HttpRequest):
    if request.method == "POST":
        form = InvitationCodeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Je account is aangemaakt! Een beheerder zal je account binnenkort activeren.",
            )
            return redirect("users:login")
        else:
            messages.error(
                request, "Er zijn fouten in het formulier. Controleer de invoer."
            )
    else:
        form = InvitationCodeRegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request: HttpRequest):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request, f"Welkom terug, {user.get_full_name() or user.username}!"
            )
            return redirect("events:list")
        else:
            # Don't show a generic error message since the form will handle specific errors
            pass
    else:
        form = CustomAuthenticationForm()
    return render(request, "users/login.html", {"form": form})


@login_required
def profile(request: HttpRequest):
    now = timezone.now()

    # Define current season (August to July of next year)
    current_year = now.year
    if now.month >= 8:  # August or later
        season_start = timezone.make_aware(datetime(current_year, 8, 1))
        season_end = timezone.make_aware(datetime(current_year + 1, 7, 31, 23, 59, 59))
    else:  # Before August
        season_start = timezone.make_aware(datetime(current_year - 1, 8, 1))
        season_end = timezone.make_aware(datetime(current_year, 7, 31, 23, 59, 59))

    # Get all events in current season
    season_events = Event.objects.filter(date__gte=season_start, date__lte=season_end)

    # Get user's attendance for season events
    user_attendance = Attendance.objects.filter(
        user=request.user, event__in=season_events
    )

    # Calculate statistics
    attended_events = user_attendance.filter(present=True).count()
    responded_events = user_attendance.count()

    # Calculate attendance rate
    if responded_events > 0:
        attendance_rate = round((attended_events / responded_events) * 100)
    else:
        attendance_rate = 0

    # Statistics by event type
    training_events = season_events.filter(event_type="training")
    training_attended = user_attendance.filter(
        event__event_type="training", present=True
    ).count()
    training_total = training_events.count()

    match_events = season_events.filter(event_type="wedstrijd")
    match_attended = user_attendance.filter(
        event__event_type="wedstrijd", present=True
    ).count()
    match_total = match_events.count()

    # Recent events (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    recent_events = season_events.filter(date__gte=thirty_days_ago)
    recent_attendance = user_attendance.filter(event__in=recent_events)
    recent_attended = recent_attendance.filter(present=True).count()
    recent_total = recent_events.count()

    context = {
        "user": request.user,
        "stats": {
            "season_start": season_start.year,
            "season_attendance_rate": attendance_rate,
            "season_present": attended_events,
            "season_total": responded_events,
            "training_present": training_attended,
            "training_total": training_total,
            "match_present": match_attended,
            "match_total": match_total,
            "recent_present": recent_attended,
            "recent_total": recent_total,
        },
    }

    return render(request, "users/profile.html", context)


@login_required
def edit_profile(request: HttpRequest):
    """Allow users to edit their own profile"""
    if request.method == "POST":
        form = PlayerProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Je profiel is succesvol bijgewerkt!")
            return redirect("users:profile")
        else:
            messages.error(
                request, "Er zijn fouten in het formulier. Controleer je invoer."
            )
    else:
        form = PlayerProfileForm(instance=request.user)

    context = {
        "form": form,
        "user": request.user,
    }

    return render(request, "users/edit_profile.html", context)


def is_staff(user):
    """Check if user is staff"""
    return user.is_staff


@user_passes_test(is_staff)
def admin_dashboard(request: HttpRequest):
    """Admin dashboard with overview statistics"""
    now = timezone.now()

    # Basic statistics
    total_players = Player.objects.count()
    active_players = Player.objects.filter(is_active=True).count()
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(date__gt=now).count()

    # Recent events with attendance
    recent_events = Event.objects.filter(date__lt=now).order_by("-date")[:5]

    # Calculate average attendance rate
    attendance_stats = []
    for event in recent_events:
        total_responses = event.attendance_set.count()
        present_count = event.attendance_set.filter(present=True).count()
        rate = (present_count / total_responses * 100) if total_responses > 0 else 0
        attendance_stats.append(
            {
                "event": event,
                "attendance_rate": round(rate, 1),
                "present_count": present_count,
                "total_responses": total_responses,
            }
        )

    # Upcoming events
    next_events = Event.objects.filter(date__gt=now).order_by("date")[:5]

    # Get invitation codes
    invitation_codes = InvitationCode.objects.filter(is_active=True).order_by(
        "-created_at"
    )[:5]

    context = {
        "total_players": total_players,
        "active_players": active_players,
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "recent_events": attendance_stats,
        "next_events": next_events,
        "invitation_codes": invitation_codes,
    }

    return render(request, "users/admin/dashboard.html", context)


@user_passes_test(is_staff)
def admin_players(request: HttpRequest):
    """Admin player management"""
    search = request.GET.get("search", "")
    status_filter = request.GET.get("status", "all")

    players = Player.objects.all()

    if search:
        players = players.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search)
        )

    if status_filter == "active":
        players = players.filter(is_active=True)
    elif status_filter == "inactive":
        players = players.filter(is_active=False)
    elif status_filter == "staff":
        players = players.filter(is_staff=True)

    players = players.order_by("last_name", "first_name")

    context = {
        "players": players,
        "search": search,
        "status_filter": status_filter,
    }

    return render(request, "users/admin/players.html", context)


@user_passes_test(is_staff)
def admin_events(request: HttpRequest):
    """Admin event management"""
    search = request.GET.get("search", "")
    event_type = request.GET.get("type", "all")
    time_filter = request.GET.get("time", "all")

    events = Event.objects.all()

    if search:
        events = events.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(location__icontains=search)
        )

    if event_type != "all":
        events = events.filter(event_type=event_type)

    now = timezone.now()
    if time_filter == "upcoming":
        events = events.filter(date__gt=now)
    elif time_filter == "past":
        events = events.filter(date__lt=now)
    elif time_filter == "today":
        events = events.filter(date__date=now.date())

    events = events.order_by("-date")

    # Add attendance stats for each event
    events_with_stats = []
    for event in events:
        total_responses = event.attendance_set.count()
        present_count = event.attendance_set.filter(present=True).count()
        attendance_rate = (
            (present_count / total_responses * 100) if total_responses > 0 else 0
        )

        events_with_stats.append(
            {
                "event": event,
                "total_responses": total_responses,
                "present_count": present_count,
                "attendance_rate": round(attendance_rate, 1),
            }
        )

    context = {
        "events_with_stats": events_with_stats,
        "search": search,
        "event_type": event_type,
        "time_filter": time_filter,
        "event_types": Event.EVENT_TYPES,
    }

    return render(request, "users/admin/events.html", context)


@user_passes_test(is_staff)
def admin_invitations(request: HttpRequest):
    """Admin invitation code management"""
    if request.method == "POST":
        # Create new invitation code
        description = request.POST.get("description", "")
        max_uses = request.POST.get("max_uses")
        expires_at = request.POST.get("expires_at")

        invitation = InvitationCode.objects.create(
            description=description,
            created_by=request.user,
            max_uses=int(max_uses) if max_uses else None,
            expires_at=(
                timezone.datetime.strptime(expires_at, "%Y-%m-%d")
                if expires_at
                else None
            ),
        )

        messages.success(
            request, f'Uitnodigingscode "{invitation.code}" is aangemaakt.'
        )
        return redirect("users:admin_invitations")

    invitations = InvitationCode.objects.all().order_by("-created_at")

    context = {
        "invitations": invitations,
    }

    return render(request, "users/admin/invitations.html", context)


@user_passes_test(is_staff)
def admin_player_detail(request: HttpRequest, player_id: int):
    """Admin player detail view"""
    player = get_object_or_404(Player, id=player_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "toggle_active":
            player.is_active = not player.is_active
            player.save()
            status = "geactiveerd" if player.is_active else "gedeactiveerd"
            messages.success(request, f"Speler {player.get_full_name()} is {status}.")

        elif action == "toggle_staff":
            player.is_staff = not player.is_staff
            player.save()
            status = "toegevoegd aan" if player.is_staff else "verwijderd uit"
            messages.success(
                request, f"Speler {player.get_full_name()} is {status} beheerders."
            )

        return redirect("users:admin_player_detail", player_id=player.id)

    # Get player's attendance statistics
    now = timezone.now()
    current_year = now.year
    if now.month >= 8:
        season_start = timezone.make_aware(datetime(current_year, 8, 1))
        season_end = timezone.make_aware(datetime(current_year + 1, 7, 31, 23, 59, 59))
    else:
        season_start = timezone.make_aware(datetime(current_year - 1, 8, 1))
        season_end = timezone.make_aware(datetime(current_year, 7, 31, 23, 59, 59))

    season_events = Event.objects.filter(date__gte=season_start, date__lte=season_end)
    player_attendance = Attendance.objects.filter(user=player, event__in=season_events)

    attended_events = player_attendance.filter(present=True).count()
    total_events = season_events.count()
    attendance_rate = (attended_events / total_events * 100) if total_events > 0 else 0

    # Recent attendance
    recent_attendance = player_attendance.select_related("event").order_by(
        "-event__date"
    )[:10]

    context = {
        "player": player,
        "attended_events": attended_events,
        "total_events": total_events,
        "attendance_rate": round(attendance_rate, 1),
        "recent_attendance": recent_attendance,
    }

    return render(request, "users/admin/player_detail.html", context)


@user_passes_test(is_staff)
def admin_toggle_invitation(request: HttpRequest, invitation_id: int):
    """Toggle invitation code active status"""
    if request.method == "POST":
        invitation = get_object_or_404(InvitationCode, id=invitation_id)
        invitation.is_active = not invitation.is_active
        invitation.save()

        status = "geactiveerd" if invitation.is_active else "gedeactiveerd"
        messages.success(request, f'Uitnodigingscode "{invitation.code}" is {status}.')

    return redirect("users:admin_invitations")
