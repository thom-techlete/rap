from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html

from .models import InvitationCode, Player


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "description",
        "is_active_display",
        "usage_display",
        "expires_display",
        "created_at",
    )
    list_filter = ("is_active", "created_at", "expires_at")
    search_fields = ("code", "description")
    readonly_fields = ("used_count", "created_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Code informatie", {"fields": ("code", "description", "is_active")}),
        ("Gebruik instellingen", {"fields": ("max_uses", "used_count", "expires_at")}),
        (
            "Metadata",
            {"fields": ("created_at", "created_by"), "classes": ("collapse",)},
        ),
    )

    def is_active_display(self, obj):
        """Show active status with colors"""
        if obj.is_active:
            is_valid, error_msg = obj.is_valid()
            if is_valid:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">✓ Actief</span>'
                )
            else:
                return format_html(
                    '<span style="color: #ffc107; font-weight: bold;">⚠ Actief ({error})</span>',
                    error=error_msg,
                )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Inactief</span>'
            )

    is_active_display.short_description = "Status"

    def usage_display(self, obj):
        """Show usage statistics"""
        if obj.max_uses:
            percentage = (obj.used_count / obj.max_uses) * 100
            color = (
                "#28a745"
                if percentage < 80
                else "#ffc107" if percentage < 100 else "#dc3545"
            )
            return format_html(
                '<span style="color: {};">{}/{} ({}%)</span>',
                color,
                obj.used_count,
                obj.max_uses,
                int(percentage),
            )
        else:
            return format_html("<span>{}/∞</span>", obj.used_count)

    usage_display.short_description = "Gebruik"

    def expires_display(self, obj):
        """Show expiration status"""
        if not obj.expires_at:
            return format_html('<span style="color: #666;">Geen vervaldatum</span>')

        if obj.expires_at < timezone.now():
            return format_html('<span style="color: #dc3545;">Verlopen</span>')
        else:
            return format_html(
                '<span style="color: #28a745;">Geldig tot {}</span>',
                obj.expires_at.strftime("%d-%m-%Y %H:%M"),
            )

    expires_display.short_description = "Vervaldatum"

    def save_model(self, request, obj, form, change):
        """Set created_by field when creating new invitation codes"""
        if not change:  # Only when creating new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Player)
class PlayerAdmin(UserAdmin):
    # Display in the admin list
    list_display = (
        "username",
        "get_full_name_display",
        "email",
        "positie",
        "rugnummer",
        "is_active",
        "date_joined",
    )

    list_filter = ("is_active", "is_staff", "positie", "date_joined")

    search_fields = ("username", "first_name", "last_name", "email", "positie")

    ordering = ("last_name", "first_name")

    # Fieldsets for the detail view
    fieldsets = UserAdmin.fieldsets + (
        (
            "Speler informatie",
            {
                "fields": (
                    "geboortedatum",
                    "telefoonnummer",
                    "positie",
                    "rugnummer",
                    "adres",
                    "foto",
                )
            },
        ),
    )

    # Fields to show when adding a new user
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Speler informatie",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "geboortedatum",
                    "telefoonnummer",
                    "positie",
                    "rugnummer",
                    "adres",
                )
            },
        ),
    )

    def get_full_name_display(self, obj):
        """Display full name with fallback to username"""
        full_name = obj.get_full_name()
        if full_name.strip():
            return full_name
        return obj.username

    get_full_name_display.short_description = "Naam"
    get_full_name_display.admin_order_field = "last_name"

    def has_change_permission(self, request, obj=None):
        """Prevent staff from editing superusers or other staff (unless they are superuser themselves)"""
        if obj is not None:
            # Allow superusers to edit anyone
            if request.user.is_superuser:
                return super().has_change_permission(request, obj)

            # Prevent staff from editing superusers
            if obj.is_superuser:
                return False

            # Prevent staff from editing other staff (but allow self-editing)
            if obj.is_staff and obj != request.user:
                return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Prevent staff from deleting superusers or other staff"""
        if obj is not None:
            # Allow superusers to delete anyone
            if request.user.is_superuser:
                return super().has_delete_permission(request, obj)

            # Prevent staff from deleting superusers
            if obj.is_superuser:
                return False

            # Prevent staff from deleting other staff
            if obj.is_staff:
                return False

        return super().has_delete_permission(request, obj)
