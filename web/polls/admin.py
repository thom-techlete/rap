from django.contrib import admin
from .models import Poll, PollOption, Vote


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 1
    fields = ["text", "order"]


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ["title", "created_by", "created_at", "is_active", "is_open", "total_votes", "unique_voters"]
    list_filter = ["is_active", "created_at", "allow_multiple_choices"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "closed_at", "total_votes", "unique_voters"]
    inlines = [PollOptionInline]
    
    fieldsets = [
        ("Basis informatie", {
            "fields": ["title", "description", "created_by"]
        }),
        ("Poll instellingen", {
            "fields": ["allow_multiple_choices", "end_date"]
        }),
        ("Status", {
            "fields": ["is_active", "closed_at", "closed_by"]
        }),
        ("Statistieken", {
            "fields": ["created_at", "total_votes", "unique_voters"],
            "classes": ["collapse"]
        })
    ]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.pk:  # editing existing object
            readonly.append("created_by")
        return readonly

    def save_model(self, request, obj, form, change):
        if not change:  # creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ["poll", "text", "order", "vote_count"]
    list_filter = ["poll"]
    search_fields = ["text", "poll__title"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["user", "poll_option", "poll", "voted_at"]
    list_filter = ["voted_at", "poll_option__poll"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "poll_option__text"]
    readonly_fields = ["voted_at"]

    def poll(self, obj):
        return obj.poll.title
    poll.short_description = "Poll"
