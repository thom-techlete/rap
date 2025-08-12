"""
Admin interface for automatic reminder logs.
"""

from django.contrib import admin

from .models import AutomaticReminderLog


@admin.register(AutomaticReminderLog)
class AutomaticReminderLogAdmin(admin.ModelAdmin):
    list_display = ["event", "reminder_type", "sent_at", "recipients_count", "success"]
    list_filter = ["reminder_type", "success", "sent_at"]
    search_fields = ["event__name", "error_message"]
    readonly_fields = [
        "event",
        "reminder_type",
        "sent_at",
        "recipients_count",
        "success",
        "error_message",
    ]
    ordering = ["-sent_at"]

    def has_add_permission(self, request):
        # Prevent manual creation - these are created automatically
        return False

    def has_change_permission(self, request, obj=None):
        # Make read-only
        return False


# Note: No models to register for notifications app
# Notification functionality is added via utils and templates
