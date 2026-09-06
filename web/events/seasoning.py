from datetime import date, datetime
from typing import cast

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Season


def get_season_for_datetime(moment: datetime | date) -> Season:
    value = (
        timezone.localdate(moment)
        if isinstance(moment, datetime) and timezone.is_aware(moment)
        else (moment.date() if isinstance(moment, datetime) else moment)
    )
    season = Season.objects.filter(start_date__lte=value, end_date__gt=value).first()
    if season is None:
        raise ValidationError("De datum valt buiten een bekend seizoen.")
    return cast(Season, season)


def season_queryset():
    return Season.objects.order_by("-is_active", "-start_date")


def get_selected_season(request):
    selected_id = request.GET.get("season")
    season = None
    if selected_id:
        try:
            season = Season.objects.get(pk=int(selected_id))
        except (TypeError, ValueError, Season.DoesNotExist):
            return _store_active(request)
    if season is None:
        stored_id = request.session.get("selected_season_id")
        if stored_id:
            try:
                season = Season.objects.get(pk=stored_id)
            except (TypeError, ValueError, Season.DoesNotExist):
                season = None
    if season is None:
        season = Season.get_active()
    request.session["selected_season_id"] = season.pk
    return season


def _store_active(request):
    season = Season.get_active()
    request.session["selected_season_id"] = season.pk
    return season
