from django.contrib import admin
from django.utils.html import format_html

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["user", "event", "present_display", "timestamp"]

    list_filter = ["present", "event__event_type", "event__date", "timestamp"]

    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "event__name",
    ]

    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def present_display(self, obj):
        """Show attendance status with colors and icons"""
        if obj.present:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Aanwezig</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Afwezig</span>'
            )

    present_display.short_description = "Status"
    present_display.admin_order_field = "present"

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related("user", "event")
