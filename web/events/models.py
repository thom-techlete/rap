import uuid
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class Event(models.Model):
    EVENT_TYPES = [
        ("training", "Training"),
        ("wedstrijd", "Wedstrijd"),
        ("uitje", "Teamuitje"),
        ("vergadering", "Vergadering"),
        ("overig", "Overig"),
    ]

    RECURRENCE_TYPES = [
        ("none", "Geen herhaling"),
        ("daily", "Dagelijks"),
        ("weekly", "Wekelijks"),
        ("biweekly", "Tweewekelijks"),
        ("monthly", "Maandelijks"),
        ("yearly", "Jaarlijks"),
    ]

    WEEKDAYS = [
        (0, "Maandag"),
        (1, "Dinsdag"),
        (2, "Woensdag"),
        (3, "Donderdag"),
        (4, "Vrijdag"),
        (5, "Zaterdag"),
        (6, "Zondag"),
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

    # Recurring event fields
    recurring_event_link_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Herhalingsgroep ID",
        help_text="Unieke ID die alle herhalende evenementen met elkaar verbindt",
    )
    recurrence_type = models.CharField(
        max_length=20,
        choices=RECURRENCE_TYPES,
        default="none",
        verbose_name="Herhalingstype",
        help_text="Hoe vaak het evenement herhaald wordt",
    )
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Einddatum herhaling",
        help_text="Laatste datum waarop het evenement herhaald wordt",
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

    @property
    def is_recurring(self):
        """Check if this event is part of a recurring series"""
        return self.recurring_event_link_id is not None

    @property
    def is_match(self):
        """Check if this event is a match (wedstrijd)"""
        return self.event_type == "wedstrijd"

    def get_attendance_count(self) -> int:
        """Get number of attendees marked as present"""
        from attendance.models import Attendance  # Lazy import

        return Attendance.objects.filter(event=self, present=True).count()

    def get_total_responses(self):
        """Get total number of attendance responses"""
        from attendance.models import Attendance  # Lazy import

        return Attendance.objects.filter(event=self).count()

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
        from attendance.models import Attendance  # Lazy import

        try:
            attendance = Attendance.objects.get(event=self, user=user)
            return attendance.present
        except Attendance.DoesNotExist:
            return None

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"pk": self.pk})

    def get_recurring_events(self):
        """Get all events in the same recurring series"""
        if not self.is_recurring:
            return Event.objects.none()
        return Event.objects.filter(
            recurring_event_link_id=self.recurring_event_link_id
        ).order_by("date")

    def get_recurrence_display(self):
        """Get human-readable recurrence description"""
        if self.recurrence_type == "none":
            return "Geen herhaling"

        type_display = dict(self.RECURRENCE_TYPES)[self.recurrence_type]
        if self.recurrence_end_date:
            return f"{type_display} tot {self.recurrence_end_date.strftime('%d-%m-%Y')}"
        return type_display

    @classmethod
    def create_recurring_events(cls, base_event_data, recurrence_type, end_date):
        """Create a series of recurring events"""

        if recurrence_type == "none":
            # Just create a single event
            return [cls.objects.create(**base_event_data)]

        # Generate a unique link ID for this series
        link_id = uuid.uuid4()
        events = []
        current_date = base_event_data["date"]

        # Calculate the interval based on recurrence type
        while current_date.date() <= end_date:
            event_data = base_event_data.copy()
            event_data["date"] = current_date
            event_data["recurring_event_link_id"] = link_id
            event_data["recurrence_type"] = recurrence_type
            event_data["recurrence_end_date"] = end_date

            events.append(cls.objects.create(**event_data))

            # Calculate next occurrence
            if recurrence_type == "daily":
                current_date += timedelta(days=1)
            elif recurrence_type == "weekly":
                current_date += timedelta(weeks=1)
            elif recurrence_type == "biweekly":
                current_date += timedelta(weeks=2)
            elif recurrence_type == "monthly":
                current_date += relativedelta(months=1)
            elif recurrence_type == "yearly":
                current_date += relativedelta(years=1)

        return events


class MatchStatistic(models.Model):
    """Model for storing match statistics like goals, assists, cards, etc."""
    
    STATISTIC_TYPES = [
        ("goal", "Doelpunt"),
        ("assist", "Assist"),
        ("yellow_card", "Gele kaart"),
        ("red_card", "Rode kaart"),
        ("substitution_in", "Wissel in"),
        ("substitution_out", "Wissel uit"),
        ("penalty_scored", "Penalty gescoord"),
        ("penalty_missed", "Penalty gemist"),
        ("own_goal", "Eigen doelpunt"),
        ("clean_sheet", "Clean sheet"), # For goalkeepers
        ("saves", "Reddingen"), # For goalkeepers
        ("man_of_the_match", "Man van de wedstrijd"),
    ]
    
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        verbose_name="Evenement",
        help_text="Het evenement waaraan deze statistiek is gekoppeld"
    )
    player = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Speler",
        help_text="De speler aan wie deze statistiek toebehoort"
    )
    statistic_type = models.CharField(
        max_length=20,
        choices=STATISTIC_TYPES,
        verbose_name="Type statistiek"
    )
    value = models.IntegerField(
        default=1,
        verbose_name="Waarde",
        help_text="Aantal voor deze statistiek (bijv. aantal doelpunten, aantal kaarten)"
    )
    minute = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Minuut",
        help_text="In welke minuut van de wedstrijd (optioneel)"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Opmerkingen",
        help_text="Extra informatie over deze statistiek"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_statistics",
        verbose_name="Toegevoegd door"
    )

    class Meta:
        verbose_name = "Wedstrijd Statistiek"
        verbose_name_plural = "Wedstrijd Statistieken"
        ordering = ["event", "minute", "statistic_type"]
        # Prevent duplicate statistics for same player/event/type/minute
        unique_together = [["event", "player", "statistic_type", "minute"]]

    def __str__(self):
        minute_info = f" ({self.minute}')" if self.minute else ""
        return f"{self.player} - {self.get_statistic_type_display()}{minute_info} - {self.event.name}"

    def clean(self):
        """Validate that statistics are only added to match events"""
        from django.core.exceptions import ValidationError
        if hasattr(self, 'event') and self.event and not self.event.is_match:
            raise ValidationError("Statistieken kunnen alleen worden toegevoegd aan wedstrijden.")
