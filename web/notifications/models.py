"""
Model for tracking automatic reminder notifications.
"""

from django.db import models
from django.utils import timezone


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
        return f"Herinnering {self.reminder_type} voor {self.event.name} - {self.sent_at.strftime('%d-%m-%Y %H:%M')}"
