from django.db import models
from django.urls import reverse
from django.utils import timezone


class Event(models.Model):
    EVENT_TYPES = [
        ("training", "Training"),
        ("wedstrijd", "Wedstrijd"),
        ("uitje", "Teamuitje"),
        ("vergadering", "Vergadering"),
        ("overig", "Overig"),
    ]

    name = models.CharField(max_length=100, verbose_name="Naam")
    description = models.TextField(blank=True, verbose_name="Beschrijving")
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        default="training",
        verbose_name="Type evenement",
    )
    date = models.DateTimeField(verbose_name="Datum en tijd")
    location = models.CharField(max_length=255, blank=True, verbose_name="Locatie")
    max_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Maximaal aantal deelnemers",
        help_text="Laat leeg voor onbeperkt",
    )
    is_mandatory = models.BooleanField(
        default=False,
        verbose_name="Verplichte aanwezigheid",
        help_text="Aanwezigheid is verplicht voor alle spelers",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date"]
        verbose_name = "Evenement"
        verbose_name_plural = "Evenementen"

    def __str__(self):
        return f"{self.name} ({self.date:%d-%m-%Y %H:%M})"

    @property
    def is_upcoming(self):
        """Check if the event is in the future"""
        return self.date > timezone.now()

    @property
    def is_today(self):
        """Check if the event is today"""
        return self.date.date() == timezone.now().date()

    def get_attendance_count(self) -> int:
        """Get number of attendees marked as present"""
        return self.attendance_set.filter(present=True).count()

    def get_total_responses(self):
        """Get total number of attendance responses"""
        return self.attendance_set.count()

    def get_attendance_rate(self):
        """Calculate attendance rate percentage"""
        total = self.get_total_responses()
        if total == 0:
            return 0
        present = self.get_attendance_count()
        return round((present / total) * 100, 1)

    def get_user_attendance_status(self, user):
        """Get the attendance status for a specific user"""
        if not user.is_authenticated:
            return None
        try:
            from attendance.models import Attendance

            attendance = self.attendance_set.get(user=user)
            return attendance.present
        except Attendance.DoesNotExist:
            return None

    def get_absolute_url(self):
        return reverse("events:edit", kwargs={"pk": self.pk})
