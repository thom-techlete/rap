"""
Custom admin configuration for django-celery-beat to make it more user-friendly.
"""

import json

from django import forms
from django.contrib import admin
from django_celery_beat.admin import PeriodicTaskAdmin as BasePeriodicTaskAdmin
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class ReminderPeriodicTaskForm(forms.ModelForm):
    """Custom form for PeriodicTask with predefined reminder types."""

    REMINDER_CHOICES = [
        ("1_week", "1 week before event"),
        ("3_days", "3 days before event"),
        ("1_day", "1 day before event"),
        ("morning_of", "Morning of event"),
    ]

    reminder_type = forms.ChoiceField(
        choices=REMINDER_CHOICES,
        required=False,
        help_text="Select reminder type for automatic event reminders",
    )

    cleanup_days = forms.IntegerField(
        initial=90,
        required=False,
        help_text="Days to keep reminder logs (for cleanup task)",
    )

    class Meta:
        model = PeriodicTask
        exclude = ["last_run_at", "total_run_count", "date_changed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If this is an existing reminder task, populate the custom fields
        if self.instance and self.instance.pk:
            try:
                kwargs_data = json.loads(self.instance.kwargs or "{}")
                if "reminder_type" in kwargs_data:
                    self.fields["reminder_type"].initial = kwargs_data["reminder_type"]
                if "days_to_keep" in kwargs_data:
                    self.fields["cleanup_days"].initial = kwargs_data["days_to_keep"]
            except (json.JSONDecodeError, KeyError):
                pass

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle reminder task configuration
        if instance.task in [
            "notifications.tasks.send_automatic_event_reminders",
            "notifications.tasks.send_event_summary_to_attendees",
        ]:
            reminder_type = self.cleaned_data.get("reminder_type")
            if reminder_type:
                instance.kwargs = json.dumps({"reminder_type": reminder_type})

        # Handle cleanup task configuration
        elif instance.task == "notifications.tasks.cleanup_old_reminder_logs":
            cleanup_days = self.cleaned_data.get("cleanup_days")
            if cleanup_days:
                instance.kwargs = json.dumps({"days_to_keep": cleanup_days})

        if commit:
            instance.save()
        return instance


class ReminderPeriodicTaskAdmin(BasePeriodicTaskAdmin):
    """Enhanced admin for PeriodicTask with reminder-specific fields."""

    form = ReminderPeriodicTaskForm

    fieldsets = (
        ("Task Information", {"fields": ("name", "task", "enabled", "description")}),
        (
            "Reminder Settings",
            {
                "fields": ("reminder_type", "cleanup_days"),
                "description": "Configure automatic reminder settings",
            },
        ),
        (
            "Schedule",
            {
                "fields": ("crontab", "interval", "solar", "one_off"),
                "description": "Choose one type of schedule",
            },
        ),
        (
            "Advanced",
            {
                "fields": (
                    "args",
                    "kwargs",
                    "queue",
                    "exchange",
                    "routing_key",
                    "priority",
                    "expires",
                    "expire_seconds",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("last_run_at", "total_run_count", "date_changed")

    list_display = ("name", "task", "enabled", "last_run_at", "total_run_count")
    list_filter = ("enabled", "task", "last_run_at")
    search_fields = ("name", "task", "description")

    def get_queryset(self, request):
        # Filter to show only reminder-related tasks by default
        qs = super().get_queryset(request)
        if not request.GET.get("all"):
            return qs.filter(
                task__in=[
                    "notifications.tasks.send_automatic_event_reminders",
                    "notifications.tasks.cleanup_old_reminder_logs",
                    "notifications.tasks.send_event_summary_to_attendees",
                ]
            )
        return qs

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_all_link"] = not request.GET.get("all")
        return super().changelist_view(request, extra_context)


# Unregister the default admin and register our custom one
admin.site.unregister(PeriodicTask)
admin.site.register(PeriodicTask, ReminderPeriodicTaskAdmin)


# Customize CrontabSchedule admin for easier time management
class CrontabScheduleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "timezone")
    list_filter = ("timezone",)
    fieldsets = (
        (
            "Time Settings",
            {
                "fields": (
                    "minute",
                    "hour",
                    "day_of_week",
                    "day_of_month",
                    "month_of_year",
                ),
                "description": 'Use * for "any" or specific values. Examples: 0=Sunday, 1=Monday, etc.',
            },
        ),
        ("Timezone", {"fields": ("timezone",)}),
    )


admin.site.unregister(CrontabSchedule)
admin.site.register(CrontabSchedule, CrontabScheduleAdmin)
