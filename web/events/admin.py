from django.contrib import admin
from django.utils.html import format_html

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "event_type",
        "date",
        "location",
        "is_mandatory",
        "recurrence_display",
        "attendance_info",
        "is_upcoming_display",
    ]
    list_filter = [
        "event_type",
        "is_mandatory",
        "recurrence_type",
        "date",
        "created_at",
    ]
    search_fields = ["name", "description", "location"]
    date_hierarchy = "date"
    ordering = ["-date"]

    fieldsets = (
        ("Basis informatie", {"fields": ("name", "description", "event_type")}),
        ("Planning", {"fields": ("date", "location")}),
        (
            "Instellingen",
            {"fields": ("is_mandatory", "max_participants"), "classes": ("collapse",)},
        ),
        (
            "Herhaling",
            {
                "fields": (
                    "recurrence_type",
                    "recurrence_end_date",
                    "recurring_event_link_id",
                ),
                "classes": ("collapse",),
                "description": "Instellingen voor herhalende evenementen",
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
                "description": "Automatisch bijgehouden informatie",
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "recurring_event_link_id")

    def attendance_info(self, obj):
        """Show attendance information with link to attendance overview"""
        total = obj.get_total_responses()
        present = obj.get_attendance_count()
        rate = obj.get_attendance_rate()

        if total == 0:
            return format_html('<span style="color: #666;">Geen reacties</span>')

        color = "#28a745" if rate >= 80 else "#ffc107" if rate >= 60 else "#dc3545"

        return format_html(
            '<span style="color: {};">{}/{} ({:.1f}%)</span>',
            color,
            present,
            total,
            rate,
        )

    attendance_info.short_description = "Aanwezigheid"

    def recurrence_display(self, obj):
        """Show recurrence information"""
        if obj.recurrence_type == "none" or not obj.recurrence_type:
            return "-"

        display = dict(Event.RECURRENCE_TYPES)[obj.recurrence_type]
        if obj.recurrence_end_date:
            display += f" (tot {obj.recurrence_end_date.strftime('%d-%m-%Y')})"

        if obj.recurring_event_link_id:
            count = Event.objects.filter(
                recurring_event_link_id=obj.recurring_event_link_id
            ).count()
            display += f" ({count} evenementen)"

        return display

    recurrence_display.short_description = "Herhaling"

    def is_upcoming_display(self, obj):
        """Show if event is upcoming with icon"""
        if obj.is_upcoming:
            return format_html('<span style="color: #28a745;">✓ Aankomend</span>')
        else:
            return format_html('<span style="color: #666;">✗ Afgelopen</span>')

    is_upcoming_display.short_description = "Status"

    def get_queryset(self, request):
        """Optimize queries by prefetching related data"""
        qs = super().get_queryset(request)
        return qs.prefetch_related("attendance_set")

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
        js = ("admin/js/custom_admin.js",)
