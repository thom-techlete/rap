from django import template
from django.utils.formats import date_format

register = template.Library()


@register.filter
def dutch_date(value):
    """Format date in Dutch dd/mm/yyyy format"""
    if not value:
        return ""
    return date_format(value, "d/m/Y")


@register.filter
def dutch_datetime(value):
    """Format datetime in Dutch dd/mm/yyyy hh:mm format"""
    if not value:
        return ""
    return date_format(value, "d/m/Y H:i")


@register.filter
def dutch_datetime_full(value):
    """Format datetime in Dutch dd/mm/yyyy hh:mm:ss format"""
    if not value:
        return ""
    return date_format(value, "d/m/Y H:i:s")


@register.filter
def dutch_time(value):
    """Format time in Dutch hh:mm format"""
    if not value:
        return ""
    return date_format(value, "H:i")
