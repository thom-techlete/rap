from datetime import timedelta

from attendance.models import Attendance
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.http import HttpRequest
from django.shortcuts import render
from django.utils import timezone

from .models import Event, MatchStatistic

User = get_user_model()


def dashboard(request: HttpRequest):
    """Main dashboard view showing overview of everything"""
    now = timezone.now()

    # Date ranges for statistics
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Basic statistics (based on past events with automatic absent for missing records)
    past_events = Event.objects.filter(date__lt=now)
    total_past_events = past_events.count()
    active_players_count = User.objects.filter(is_active=True).count()

    # Total possible attendance responses (all players × all past events)
    total_possible_responses = total_past_events * active_players_count

    # Actual present attendances
    total_present_attendances = Attendance.objects.filter(
        event__in=past_events, present=True
    ).count()

    stats = {
        "total_events": Event.objects.count(),
        "upcoming_events": Event.objects.filter(date__gt=now).count(),
        "events_this_week": Event.objects.filter(
            date__gte=week_ago, date__lte=now + timedelta(days=7)
        ).count(),
        "active_players": active_players_count,
        "total_attendance_responses": total_possible_responses,
        "total_present_attendances": total_present_attendances,
    }

    # Calculate team-wide attendance rate (including automatic absences)
    if total_possible_responses > 0:
        stats["team_attendance_rate"] = round(
            (total_present_attendances / total_possible_responses) * 100, 1
        )
    else:
        stats["team_attendance_rate"] = 0

    # Recent events (last 5 past events and next 5 upcoming events)
    recent_past_events = Event.objects.filter(date__lt=now).order_by("-date")[:3]

    upcoming_events = Event.objects.filter(date__gt=now).order_by("date")[:5]

    # Add attendance information for upcoming events if user is authenticated
    if request.user.is_authenticated:
        from django.db.models import Prefetch

        user_attendance_prefetch = Prefetch(
            "attendance_set",
            queryset=Attendance.objects.filter(user=request.user),
            to_attr="user_attendance",
        )
        upcoming_events = upcoming_events.prefetch_related(user_attendance_prefetch)

    # Next event happening today or soon
    next_event = Event.objects.filter(date__gt=now).order_by("date").first()
    today_events = Event.objects.filter(date__date=now.date())

    # Player attendance ranking
    player_rankings = calculate_player_rankings()

    # Recent attendance activity (for the activity feed)
    recent_attendance = (
        Attendance.objects.select_related("user", "event")
        .filter(timestamp__gte=week_ago)
        .order_by("-timestamp")[:10]
    )

    # Event type statistics
    event_type_stats = (
        Event.objects.values("event_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Attendance rate for recent events
    recent_events_with_attendance = Event.objects.filter(
        date__gte=month_ago, date__lt=now
    ).annotate(
        total_responses=Count("attendance"),
        present_count=Count("attendance", filter=Q(attendance__present=True)),
    )

    # Match statistics (only include completed matches)
    match_stats = calculate_match_statistics()

    context = {
        "stats": stats,
        "recent_past_events": recent_past_events,
        "upcoming_events": upcoming_events,
        "next_event": next_event,
        "today_events": today_events,
        "player_rankings": player_rankings,
        "recent_attendance": recent_attendance,
        "event_type_stats": event_type_stats,
        "recent_events_with_attendance": recent_events_with_attendance,
        "match_stats": match_stats,
        "now": now,
    }

    return render(request, "dashboard/main.html", context)


def calculate_player_rankings():
    """Calculate player attendance rankings"""
    # Get all active players
    active_players = User.objects.filter(is_active=True)

    # Get all past events (events that have already happened)
    now = timezone.now()
    past_events = Event.objects.filter(date__lt=now)

    rankings = []

    for player in active_players:
        # Get all attendance records for this player
        attendances = Attendance.objects.filter(user=player)

        # Calculate total events this player should have attended (past events)
        total_past_events = past_events.count()

        if total_past_events == 0:
            attendance_rate = 0
            present_count = 0
        else:
            # Count how many past events this player was marked as present
            present_count = attendances.filter(
                event__in=past_events, present=True
            ).count()

            # Attendance rate is based on past events only
            attendance_rate = (present_count / total_past_events) * 100

        # Get recent attendance (last 5 past events)
        recent_past_events = past_events.order_by("-date")[:5]
        recent_attendance_rate = 0
        if recent_past_events.count() > 0:
            recent_present = attendances.filter(
                event__in=recent_past_events, present=True
            ).count()
            recent_attendance_rate = (recent_present / recent_past_events.count()) * 100

        rankings.append(
            {
                "player": player,
                "total_events": total_past_events,
                "present_count": present_count,
                "attendance_rate": round(attendance_rate, 1),
                "recent_attendance_rate": round(recent_attendance_rate, 1),
                "recent_attendances": list(
                    attendances.filter(event__in=recent_past_events).order_by(
                        "-event__date"
                    )
                ),
            }
        )

    # Sort by attendance rate (descending), then by total events
    rankings.sort(key=lambda x: (-x["attendance_rate"], -x["total_events"]))

    # Add ranking position
    for i, ranking in enumerate(rankings, 1):
        ranking["position"] = i

    return rankings


def calculate_match_statistics():
    """Calculate comprehensive match statistics for dashboard"""
    now = timezone.now()
    
    # Get all completed matches (past events that are matches)
    completed_matches = Event.objects.filter(
        date__lt=now, 
        event_type="wedstrijd"
    )
    
    if not completed_matches.exists():
        return {
            "total_matches": 0,
            "total_goals": 0,
            "total_assists": 0,
            "total_cards": 0,
            "top_goalscorers": [],
            "top_assisters": [],
            "most_carded": [],
            "recent_statistics": [],
        }
    
    # Total statistics
    total_matches = completed_matches.count()
    total_goals = MatchStatistic.objects.filter(
        event__in=completed_matches,
        statistic_type='goal'
    ).aggregate(total=Sum('value'))['total'] or 0
    
    total_assists = MatchStatistic.objects.filter(
        event__in=completed_matches,
        statistic_type='assist'
    ).aggregate(total=Sum('value'))['total'] or 0
    
    total_cards = MatchStatistic.objects.filter(
        event__in=completed_matches,
        statistic_type__in=['yellow_card', 'red_card']
    ).aggregate(total=Sum('value'))['total'] or 0
    
    # Top goalscorers
    top_goalscorers = (
        MatchStatistic.objects
        .filter(event__in=completed_matches, statistic_type='goal')
        .values('player__first_name', 'player__last_name', 'player__username')
        .annotate(total_goals=Sum('value'))
        .order_by('-total_goals')[:5]
    )
    
    # Top assisters
    top_assisters = (
        MatchStatistic.objects
        .filter(event__in=completed_matches, statistic_type='assist')
        .values('player__first_name', 'player__last_name', 'player__username')
        .annotate(total_assists=Sum('value'))
        .order_by('-total_assists')[:5]
    )
    
    # Most carded players
    most_carded = (
        MatchStatistic.objects
        .filter(event__in=completed_matches, statistic_type__in=['yellow_card', 'red_card'])
        .values('player__first_name', 'player__last_name', 'player__username')
        .annotate(total_cards=Sum('value'))
        .order_by('-total_cards')[:5]
    )
    
    # Recent statistics (last 10 statistics added)
    recent_statistics = (
        MatchStatistic.objects
        .filter(event__in=completed_matches)
        .select_related('player', 'event')
        .order_by('-created_at')[:10]
    )
    
    return {
        "total_matches": total_matches,
        "total_goals": total_goals,
        "total_assists": total_assists,
        "total_cards": total_cards,
        "top_goalscorers": top_goalscorers,
        "top_assisters": top_assisters,
        "most_carded": most_carded,
        "recent_statistics": recent_statistics,
    }
