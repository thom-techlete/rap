from datetime import timedelta, date
from calendar import monthrange
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, Avg, F, Min, Max
from django.http import HttpRequest
from django.shortcuts import render
from django.utils import timezone
from django.db.models.functions import TruncMonth, TruncWeek

from .models import Event, MatchStatistic
from attendance.models import Attendance

User = get_user_model()


@login_required
def analytics_dashboard(request: HttpRequest):
    """Comprehensive analytics dashboard showing detailed insights across all data"""
    now = timezone.now()
    
    # Get analytics data
    event_analytics = calculate_event_analytics()
    attendance_analytics = calculate_attendance_analytics()
    match_analytics = calculate_detailed_match_analytics()
    response_time_analytics = calculate_response_time_analytics()
    player_analytics = calculate_player_analytics()
    
    context = {
        "event_analytics": event_analytics,
        "attendance_analytics": attendance_analytics,
        "match_analytics": match_analytics,
        "response_time_analytics": response_time_analytics,
        "player_analytics": player_analytics,
        "now": now,
    }
    
    return render(request, "events/analytics_dashboard.html", context)


def calculate_event_analytics():
    """Calculate comprehensive event analytics"""
    now = timezone.now()
    
    # Event type distribution
    event_types = (
        Event.objects
        .values("event_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    # Training and match counts
    training_count = Event.objects.filter(event_type="training").count()
    match_count = Event.objects.filter(event_type="wedstrijd").count()
    
    # Events over time (monthly)
    events_by_month = (
        Event.objects
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    
    # Events by location (top 10)
    events_by_location = (
        Event.objects
        .exclude(location="")
        .values("location")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    
    # Mandatory vs optional events
    mandatory_stats = Event.objects.aggregate(
        total=Count("id"),
        mandatory=Count("id", filter=Q(is_mandatory=True)),
        optional=Count("id", filter=Q(is_mandatory=False))
    )
    
    # Recurring vs one-time events
    recurring_stats = Event.objects.aggregate(
        total=Count("id"),
        recurring=Count("id", filter=Q(recurrence_type__isnull=False) & ~Q(recurrence_type="none")),
        oneTime=Count("id", filter=Q(recurrence_type="none"))
    )
    
    # Events per day of week
    events_by_weekday = []
    weekdays = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
    for i in range(7):
        # Django week_day: 1=Sunday, 2=Monday, ..., 7=Saturday
        # We want: 0=Monday, 1=Tuesday, ..., 6=Sunday
        # So we map: Monday(i=0) -> week_day=2, Tuesday(i=1) -> week_day=3, ..., Sunday(i=6) -> week_day=1
        week_day = (i + 2) % 7
        if week_day == 0:
            week_day = 7
        count = Event.objects.filter(date__week_day=week_day).count()
        events_by_weekday.append({"day": weekdays[i], "count": count})
    
    return {
        "event_types": list(event_types),
        "training_count": training_count,
        "match_count": match_count,
        "events_by_month": list(events_by_month),
        "events_by_location": list(events_by_location),
        "mandatory_stats": mandatory_stats,
        "recurring_stats": recurring_stats,
        "events_by_weekday": events_by_weekday,
    }


def calculate_attendance_analytics():
    """Calculate comprehensive attendance analytics"""
    now = timezone.now()
    
    # Overall attendance rate over time (monthly)
    attendance_by_month = []
    for i in range(12):
        month_start = now.replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        
        events_in_month = Event.objects.filter(
            date__gte=month_start,
            date__lte=month_end,
            date__lt=now
        )
        
        if events_in_month.exists():
            total_responses = Attendance.objects.filter(event__in=events_in_month).count()
            present_responses = Attendance.objects.filter(
                event__in=events_in_month, present=True
            ).count()
            
            rate = (present_responses / total_responses * 100) if total_responses > 0 else 0
            
            attendance_by_month.append({
                "month": month_start.strftime("%Y-%m"),
                "month_name": month_start.strftime("%B %Y"),
                "rate": round(rate, 1),
                "present": present_responses,
                "total": total_responses,
            })
    
    attendance_by_month.reverse()  # Show oldest to newest
    
    # Attendance by event type
    attendance_by_event_type = []
    for event_type, event_type_name in Event.EVENT_TYPES:
        events = Event.objects.filter(event_type=event_type, date__lt=now)
        if events.exists():
            total_responses = Attendance.objects.filter(event__in=events).count()
            present_responses = Attendance.objects.filter(
                event__in=events, present=True
            ).count()
            
            rate = (present_responses / total_responses * 100) if total_responses > 0 else 0
            
            attendance_by_event_type.append({
                "event_type": event_type_name,
                "rate": round(rate, 1),
                "present": present_responses,
                "total": total_responses,
            })
    
    # Attendance patterns by day of week
    attendance_by_weekday = []
    weekdays = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
    for i in range(7):
        events = Event.objects.filter(date__week_day=i+1, date__lt=now)
        if events.exists():
            total_responses = Attendance.objects.filter(event__in=events).count()
            present_responses = Attendance.objects.filter(
                event__in=events, present=True
            ).count()
            
            rate = (present_responses / total_responses * 100) if total_responses > 0 else 0
            
            attendance_by_weekday.append({
                "day": weekdays[i],
                "rate": round(rate, 1),
                "present": present_responses,
                "total": total_responses,
            })
    
    return {
        "attendance_by_month": attendance_by_month,
        "attendance_by_event_type": attendance_by_event_type,
        "attendance_by_weekday": attendance_by_weekday,
    }


def calculate_detailed_match_analytics():
    """Calculate detailed match statistics analytics"""
    now = timezone.now()
    
    # Get all completed matches
    completed_matches = Event.objects.filter(
        date__lt=now, 
        event_type="wedstrijd"
    )
    
    if not completed_matches.exists():
        return {
            "total_matches": 0,
            "goals_by_month": [],
            "top_performers": {},
            "statistics_distribution": [],
            "recent_match_stats": [],
        }
    
    # Goals scored over time (monthly)
    goals_by_month = []
    for i in range(6):  # Last 6 months
        month_start = now.replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        
        matches_in_month = completed_matches.filter(
            date__gte=month_start,
            date__lte=month_end
        )
        
        goals = MatchStatistic.objects.filter(
            event__in=matches_in_month,
            statistic_type="goal"
        ).aggregate(total=Sum("value"))["total"] or 0
        
        goals_by_month.append({
            "month": month_start.strftime("%Y-%m"),
            "month_name": month_start.strftime("%B"),
            "goals": goals,
        })
    
    goals_by_month.reverse()
    
    # Top performers in different categories
    top_performers = {}
    
    # Top goalscorers (all time)
    top_performers["goalscorers"] = list(
        MatchStatistic.objects
        .filter(event__in=completed_matches, statistic_type="goal")
        .values("player__first_name", "player__last_name", "player__username")
        .annotate(total=Sum("value"))
        .order_by("-total")[:10]
    )
    
    # Top assisters
    top_performers["assisters"] = list(
        MatchStatistic.objects
        .filter(event__in=completed_matches, statistic_type="assist")
        .values("player__first_name", "player__last_name", "player__username")
        .annotate(total=Sum("value"))
        .order_by("-total")[:10]
    )
    
    # Most cards
    top_performers["most_cards"] = list(
        MatchStatistic.objects
        .filter(event__in=completed_matches, statistic_type__in=["yellow_card", "red_card"])
        .values("player__first_name", "player__last_name", "player__username")
        .annotate(total=Sum("value"))
        .order_by("-total")[:10]
    )
    
    # Statistics distribution
    statistics_distribution = list(
        MatchStatistic.objects
        .filter(event__in=completed_matches)
        .values("statistic_type")
        .annotate(count=Sum("value"))
        .order_by("-count")
    )
    
    # Recent match performance (last 5 matches)
    recent_matches = completed_matches.order_by("-date")[:5]
    recent_match_stats = []
    
    for match in recent_matches:
        stats = MatchStatistic.objects.filter(event=match)
        match_data = {
            "event": match,
            "goals": stats.filter(statistic_type="goal").aggregate(total=Sum("value"))["total"] or 0,
            "assists": stats.filter(statistic_type="assist").aggregate(total=Sum("value"))["total"] or 0,
            "yellow_cards": stats.filter(statistic_type="yellow_card").aggregate(total=Sum("value"))["total"] or 0,
            "red_cards": stats.filter(statistic_type="red_card").aggregate(total=Sum("value"))["total"] or 0,
        }
        recent_match_stats.append(match_data)
    
    return {
        "total_matches": completed_matches.count(),
        "goals_by_month": goals_by_month,
        "top_performers": top_performers,
        "statistics_distribution": statistics_distribution,
        "recent_match_stats": recent_match_stats,
    }


def calculate_response_time_analytics():
    """Calculate response time analytics for attendance"""
    now = timezone.now()
    
    # Response time distribution (how quickly people respond to events)
    response_times = []
    
    # Get events from the past 3 months with attendance data
    three_months_ago = now - timedelta(days=90)
    recent_events = Event.objects.filter(
        date__gte=three_months_ago,
        date__lte=now
    )
    
    for event in recent_events:
        attendances = Attendance.objects.filter(event=event)
        for attendance in attendances:
            if attendance.timestamp and event.created_at:
                response_time = (attendance.timestamp - event.created_at).total_seconds() / 3600  # hours
                if response_time >= 0:  # Only count positive response times
                    response_times.append({
                        "event_id": event.id,
                        "event_name": event.name,
                        "hours": round(response_time, 2),
                        "present": attendance.present,
                    })
    
    # Categorize response times
    response_categories = {
        "immediate": 0,  # < 1 hour
        "quick": 0,      # 1-6 hours
        "same_day": 0,   # 6-24 hours
        "next_day": 0,   # 1-2 days
        "late": 0,       # > 2 days
    }
    
    for response in response_times:
        hours = response["hours"]
        if hours < 1:
            response_categories["immediate"] += 1
        elif hours < 6:
            response_categories["quick"] += 1
        elif hours < 24:
            response_categories["same_day"] += 1
        elif hours < 48:
            response_categories["next_day"] += 1
        else:
            response_categories["late"] += 1
    
    # Average response time
    avg_response_time = sum(r["hours"] for r in response_times) / len(response_times) if response_times else 0
    
    return {
        "response_categories": response_categories,
        "avg_response_time": round(avg_response_time, 1),
        "total_responses": len(response_times),
        "response_details": response_times[:20],  # Show latest 20 for detailed view
    }


def calculate_player_analytics():
    """Calculate detailed player performance analytics"""
    now = timezone.now()
    
    # Active players
    active_players = User.objects.filter(is_active=True)
    
    # Player attendance streaks and patterns
    player_stats = []
    
    # Get past events for calculation
    past_events = Event.objects.filter(date__lt=now).order_by("-date")
    
    for player in active_players:
        attendances = Attendance.objects.filter(
            user=player,
            event__in=past_events
        ).order_by("-event__date")
        
        total_events = past_events.count()
        attended = attendances.filter(present=True).count()
        attendance_rate = (attended / total_events * 100) if total_events > 0 else 0
        
        # Calculate current streak
        current_streak = 0
        for attendance in attendances:
            if attendance.present:
                current_streak += 1
            else:
                break
        
        # Recent performance (last 10 events)
        recent_attendances = attendances[:10]
        recent_attended = sum(1 for att in recent_attendances if att.present)
        recent_rate = (recent_attended / min(10, len(recent_attendances)) * 100) if len(recent_attendances) > 0 else 0
        
        player_stats.append({
            "player": player,
            "total_events": total_events,
            "attended": attended,
            "attendance_rate": round(attendance_rate, 1),
            "recent_rate": round(recent_rate, 1),
            "current_streak": current_streak,
        })
    
    # Sort by attendance rate
    player_stats.sort(key=lambda x: x["attendance_rate"], reverse=True)
    
    # Team performance trends
    team_trends = []
    for i in range(12):  # Last 12 months
        month_start = now.replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        
        events_in_month = past_events.filter(
            date__gte=month_start,
            date__lte=month_end
        )
        
        if events_in_month.exists():
            total_possible = events_in_month.count() * active_players.count()
            actual_present = Attendance.objects.filter(
                event__in=events_in_month,
                present=True
            ).count()
            
            team_rate = (actual_present / total_possible * 100) if total_possible > 0 else 0
            
            team_trends.append({
                "month": month_start.strftime("%Y-%m"),
                "month_name": month_start.strftime("%B"),
                "rate": round(team_rate, 1),
                "events": events_in_month.count(),
            })
    
    team_trends.reverse()
    
    return {
        "player_stats": player_stats,
        "team_trends": team_trends,
        "total_active_players": active_players.count(),
    }