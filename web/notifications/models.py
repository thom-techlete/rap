"""
Models for tracking automatic reminder notifications and scheduling configuration.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ScheduleConfiguration(models.Model):
    """
    Global configuration for task scheduling.
    """

    TASK_CHOICES = [
        (
            "notifications.tasks.send_automatic_event_reminders",
            "Automatische evenement herinneringen",
        ),
        (
            "notifications.tasks.cleanup_old_reminder_logs",
            "Opruimen oude herinnering logs",
        ),
        (
            "notifications.tasks.send_event_summary_to_attendees",
            "Notificatie evenement voor aanwezigen",
        ),
    ]

    REMINDER_TYPE_CHOICES = [
        ("1_week", "1 week van tevoren"),
        ("3_days", "3 dagen van tevoren"),
        ("1_day", "1 dag van tevoren"),
        ("morning_of", "Dag van het evenement"),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Configuratie naam",
        help_text="Unieke naam voor deze taak configuratie",
    )
    task = models.CharField(
        max_length=200,
        choices=TASK_CHOICES,
        verbose_name="Taak",
        help_text="Welke taak moet uitgevoerd worden",
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPE_CHOICES,
        blank=True,
        verbose_name="Type herinnering",
        help_text="Voor reminder taken, welk type herinnering",
    )

    # Cron schedule fields
    minute = models.CharField(
        max_length=100,
        default="0",
        verbose_name="Minuut",
        help_text="Minuut (0-59, *, */5, etc.)",
    )
    hour = models.CharField(
        max_length=100,
        default="9",
        verbose_name="Uur",
        help_text="Uur (0-23, *, */2, etc.)",
    )
    day_of_week = models.CharField(
        max_length=100,
        default="*",
        verbose_name="Dag van de week",
        help_text="Dag van de week (0=Zondag, 1=Maandag, *, etc.)",
    )
    day_of_month = models.CharField(
        max_length=100,
        default="*",
        verbose_name="Dag van de maand",
        help_text="Dag van de maand (1-31, *, */2, etc.)",
    )
    month_of_year = models.CharField(
        max_length=100,
        default="*",
        verbose_name="Maand van het jaar",
        help_text="Maand van het jaar (1-12, *, etc.)",
    )

    enabled = models.BooleanField(
        default=True, verbose_name="Actief", help_text="Of deze taak actief is"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Taak configuratie"
        verbose_name_plural = "Taak configuraties"
        ordering = ["name"]

    def __str__(self):
        # Manual lookup for task display
        task_display = dict(self.TASK_CHOICES).get(self.task, self.task)
        return f"{self.name} - {task_display}"

    def clean(self):
        # Validate that reminder tasks have a reminder_type
        if "reminder" in self.task and not self.reminder_type:
            raise ValidationError(
                "Herinnering taken moeten een herinnering type hebben"
            )

    def get_cron_expression(self):
        """Get human readable cron expression"""
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month_of_year} {self.day_of_week}"


class EventScheduleOverride(models.Model):
    """
    Per-event scheduling overrides.
    """

    event = models.OneToOneField(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="schedule_override",
        verbose_name="Evenement",
    )

    configuration = models.ForeignKey(
        ScheduleConfiguration,
        on_delete=models.CASCADE,
        verbose_name="Basis configuratie",
        help_text="De basis configuratie waarop deze override gebaseerd is",
    )

    # Override fields (if blank, use configuration defaults)
    override_minute = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Override minuut",
        help_text="Laat leeg om basis configuratie te gebruiken",
    )
    override_hour = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Override uur",
        help_text="Laat leeg om basis configuratie te gebruiken",
    )
    override_day_of_week = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Override dag van de week",
        help_text="Laat leeg om basis configuratie te gebruiken",
    )
    override_day_of_month = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Override dag van de maand",
        help_text="Laat leeg om basis configuratie te gebruiken",
    )
    override_month_of_year = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Override maand van het jaar",
        help_text="Laat leeg om basis configuratie te gebruiken",
    )

    enabled = models.BooleanField(
        default=True, verbose_name="Actief", help_text="Of deze override actief is"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evenement taak override"
        verbose_name_plural = "Evenement taak overrides"
        ordering = ["event__date"]

    def __str__(self):
        return f"Override voor {self.event.name} - {self.configuration.name}"

    def get_effective_schedule(self):
        """Get the effective schedule (overrides applied to base configuration)"""
        return {
            "minute": self.override_minute or self.configuration.minute,
            "hour": self.override_hour or self.configuration.hour,
            "day_of_week": self.override_day_of_week or self.configuration.day_of_week,
            "day_of_month": self.override_day_of_month
            or self.configuration.day_of_month,
            "month_of_year": self.override_month_of_year
            or self.configuration.month_of_year,
        }

    def get_effective_cron_expression(self):
        """Get human readable effective cron expression"""
        schedule = self.get_effective_schedule()
        return f"{schedule['minute']} {schedule['hour']} {schedule['day_of_month']} {schedule['month_of_year']} {schedule['day_of_week']}"


class AutomaticReminderLog(models.Model):
    """
    Tracks automatic reminders sent for events to prevent duplicates.
    """

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="automatic_reminders",
        verbose_name="Evenement",
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=[
            ("1_week", "1 week van tevoren"),
            ("3_days", "3 dagen van tevoren"),
            ("1_day", "1 dag van tevoren"),
            ("morning_of", "Dag van het evenement"),
        ],
        default="1_week",
        verbose_name="Type herinnering",
    )
    sent_at = models.DateTimeField(default=timezone.now, verbose_name="Verzonden op")
    recipients_count = models.PositiveIntegerField(
        default=0, verbose_name="Aantal ontvangers"
    )
    success = models.BooleanField(default=True, verbose_name="Succesvol verzonden")
    error_message = models.TextField(blank=True, verbose_name="Foutmelding")

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "Automatische herinnering"
        verbose_name_plural = "Automatische herinneringen"
        unique_together = ["event", "reminder_type"]  # Prevent duplicate reminders

    def __str__(self):
        # Convert to local timezone for display
        local_sent_time = timezone.localtime(self.sent_at)
        return f"Herinnering {self.reminder_type} voor {self.event.name} - {local_sent_time.strftime('%d-%m-%Y %H:%M')}"
