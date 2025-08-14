"""
Admin interface for notifications scheduling and automatic reminder logs.
"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html

from .models import AutomaticReminderLog, ScheduleConfiguration, EventScheduleOverride
from .utils import sync_periodic_tasks


@admin.register(ScheduleConfiguration)
class ScheduleConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "task",
        "reminder_type",
        "get_cron_display",
        "enabled",
        "updated_at",
    )
    list_filter = ("task", "reminder_type", "enabled")
    search_fields = ("name", "task")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Basis informatie", {
            "fields": ("name", "task", "reminder_type", "enabled")
        }),
        ("Schema configuratie", {
            "fields": ("minute", "hour", "day_of_week", "day_of_month", "month_of_year"),
            "description": "Configureer wanneer de taak uitgevoerd moet worden. Gebruik * voor 'alle' of specifieke waarden."
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def get_cron_display(self, obj):
        return obj.get_cron_expression()
    get_cron_display.short_description = "Cron expressie"
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Sync with Celery beat after saving
        try:
            sync_periodic_tasks()
            messages.success(request, f"Configuratie '{obj.name}' opgeslagen en gesynchroniseerd met Celery beat.")
        except Exception as e:
            messages.warning(request, f"Configuratie opgeslagen, maar synchronisatie met Celery beat is mislukt: {e}")


@admin.register(EventScheduleOverride)
class EventScheduleOverrideAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "configuration",
        "get_effective_cron_display",
        "enabled",
        "updated_at",
    )
    list_filter = ("configuration", "enabled", "event__event_type")
    search_fields = ("event__name", "configuration__name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("event",)
    
    fieldsets = (
        ("Basis informatie", {
            "fields": ("event", "configuration", "enabled")
        }),
        ("Schema overrides", {
            "fields": ("override_minute", "override_hour", "override_day_of_week", "override_day_of_month", "override_month_of_year"),
            "description": "Laat velden leeg om de basis configuratie te gebruiken. Vul alleen in wat je wilt overschrijven."
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def get_effective_cron_display(self, obj):
        return obj.get_effective_cron_expression()
    get_effective_cron_display.short_description = "Effectieve cron expressie"
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Sync with Celery beat after saving
        try:
            sync_periodic_tasks()
            messages.success(request, f"Override voor '{obj.event.name}' opgeslagen en gesynchroniseerd met Celery beat.")
        except Exception as e:
            messages.warning(request, f"Override opgeslagen, maar synchronisatie met Celery beat is mislukt: {e}")


@admin.register(AutomaticReminderLog)
class AutomaticReminderLogAdmin(admin.ModelAdmin):
    list_display = [
        "event", 
        "reminder_type", 
        "sent_at", 
        "recipients_count", 
        "success"
    ]
    list_filter = [
        "reminder_type", 
        "success", 
        "sent_at"
    ]
    search_fields = [
        "event__name", 
        "error_message"
    ]
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
