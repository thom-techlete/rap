from events.models import Season
from events.seasoning import get_selected_season, season_queryset


def seasons(request):
    if not request.user.is_authenticated:
        return {}
    try:
        selected = get_selected_season(request)
        return {"selected_season": selected, "seasons": season_queryset()}
    except Season.DoesNotExist:
        return {}
