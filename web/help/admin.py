from django.contrib import admin
from .models import BugReport


@admin.register(BugReport)
class BugReportAdmin(admin.ModelAdmin):
    """Admin interface for BugReport model."""
    
    list_display = [
        'id', 
        'title', 
        'reported_by', 
        'status', 
        'priority', 
        'assigned_to', 
        'reported_at'
    ]
    list_filter = [
        'status', 
        'priority', 
        'reported_at', 
        'resolved_at'
    ]
    search_fields = [
        'title', 
        'description', 
        'reported_by__username', 
        'reported_by__first_name', 
        'reported_by__last_name'
    ]
    readonly_fields = [
        'reported_at', 
        'resolved_at'
    ]
    
    fieldsets = (
        ('Bug Informatie', {
            'fields': (
                'title', 
                'description', 
                'steps_to_reproduce', 
                'expected_behavior', 
                'actual_behavior', 
                'browser_info'
            )
        }),
        ('Status & Beheer', {
            'fields': (
                'status', 
                'priority', 
                'assigned_to', 
                'admin_notes'
            )
        }),
        ('Tijdstempels', {
            'fields': (
                'reported_by', 
                'reported_at', 
                'resolved_by', 
                'resolved_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make reported_by readonly for existing objects."""
        if obj:  # editing an existing object
            return self.readonly_fields + ('reported_by',)
        return self.readonly_fields
