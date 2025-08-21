"""
Admin interface for notifications scheduling and automatic reminder logs.
"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html

from .models import AutomaticReminderLog, ScheduleConfiguration, EventScheduleOverride, PushSubscription, PushNotificationLog
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


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "get_endpoint_display", "is_active", "created_at", "last_used")
    list_filter = ("is_active", "created_at", "last_used")
    search_fields = ("user__email", "user__first_name", "user__last_name", "endpoint")
    ordering = ("-created_at",)
    
    fieldsets = (
        ("Gebruiker informatie", {
            "fields": ("user", "is_active")
        }),
        ("Subscription details", {
            "fields": ("endpoint", "p256dh_key", "auth_key"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("user_agent", "created_at", "last_used"),
            "classes": ("collapse",)
        })
    )
    
    readonly_fields = ("created_at", "last_used")
    
    def get_endpoint_display(self, obj):
        if len(obj.endpoint) > 50:
            return f"{obj.endpoint[:50]}..."
        return obj.endpoint
    get_endpoint_display.short_description = "Endpoint"
    
    actions = ["deactivate_subscriptions", "test_subscriptions"]
    
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} subscriptions gedeactiveerd.")
    deactivate_subscriptions.short_description = "Geselecteerde subscriptions deactiveren"
    
    def test_subscriptions(self, request, queryset):
        from .tasks import send_push_notification
        
        test_data = {
            'title': 'Test van Admin',
            'body': 'Dit is een test notificatie verzonden vanuit de admin.',
            'icon': '/static/media/icons/icon-192x192.png'
        }
        
        sent_count = 0
        for subscription in queryset.filter(is_active=True):
            try:
                send_push_notification.delay(subscription.id, test_data)
                sent_count += 1
            except Exception:
                pass
        
        self.message_user(request, f"Test notificaties verzonden naar {sent_count} subscriptions.")
    test_subscriptions.short_description = "Test notificatie naar geselecteerde subscriptions"


@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = ("get_user", "title", "success", "response_code", "sent_at")
    list_filter = ("success", "response_code", "sent_at")
    search_fields = ("subscription__user__email", "title", "body", "error_message")
    ordering = ("-sent_at",)
    
    fieldsets = (
        ("Notificatie details", {
            "fields": ("subscription", "title", "body", "url", "icon")
        }),
        ("Verzend resultaten", {
            "fields": ("success", "response_code", "error_message", "sent_at")
        })
    )
    
    readonly_fields = ("subscription", "title", "body", "url", "icon", 
                      "sent_at", "success", "response_code", "error_message")
    
    def get_user(self, obj):
        return obj.subscription.user.get_full_name()
    get_user.short_description = "Gebruiker"
    
    def has_add_permission(self, request):
        return False  # These are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # These are read-only logs
