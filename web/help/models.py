from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.urls import reverse

User = get_user_model()


class BugReport(models.Model):
    """Model for bug reports submitted by users."""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In behandeling'),
        ('resolved', 'Opgelost'),
        ('closed', 'Gesloten'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Laag'),
        ('medium', 'Gemiddeld'),
        ('high', 'Hoog'),
        ('critical', 'Kritiek'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name="Titel",
        help_text="Korte beschrijving van de bug"
    )
    description = models.TextField(
        verbose_name="Beschrijving",
        help_text="Gedetailleerde beschrijving van het probleem"
    )
    steps_to_reproduce = models.TextField(
        blank=True,
        verbose_name="Stappen om te reproduceren",
        help_text="Hoe kan de bug gereproduceerd worden?"
    )
    expected_behavior = models.TextField(
        blank=True,
        verbose_name="Verwacht gedrag",
        help_text="Wat had er moeten gebeuren?"
    )
    actual_behavior = models.TextField(
        blank=True,
        verbose_name="Werkelijk gedrag",
        help_text="Wat gebeurde er daadwerkelijk?"
    )
    browser_info = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Browser informatie",
        help_text="Welke browser en versie gebruikte je?"
    )
    
    # Metadata
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bug_reports",
        verbose_name="Gerapporteerd door"
    )
    reported_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Gerapporteerd op"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Prioriteit"
    )
    
    # Admin fields
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_bug_reports",
        verbose_name="Toegewezen aan"
    )
    admin_notes = models.TextField(
        blank=True,
        verbose_name="Beheerder notities",
        help_text="Interne notities voor beheerders"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Opgelost op"
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_bug_reports",
        verbose_name="Opgelost door"
    )
    
    class Meta:
        ordering = ["-reported_at"]
        verbose_name = "Bug Rapport"
        verbose_name_plural = "Bug Rapporten"
    
    def __str__(self):
        return f"#{self.id} - {self.title}"
    
    def get_absolute_url(self):
        return reverse("help:bug_detail", kwargs={"pk": self.pk})
    
    def mark_resolved(self, user=None):
        """Mark the bug report as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        self.save()
    
    def mark_closed(self, user=None):
        """Mark the bug report as closed."""
        self.status = 'closed'
        if not self.resolved_at:
            self.resolved_at = timezone.now()
        if user and not self.resolved_by:
            self.resolved_by = user
        self.save()
    
    @property
    def is_open(self):
        """Check if bug report is still open for work."""
        return self.status in ['open', 'in_progress']
    
    @property
    def status_display(self):
        """Get display value for status."""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def priority_display(self):
        """Get display value for priority."""
        return dict(self.PRIORITY_CHOICES).get(self.priority, self.priority)
    
    @property
    def priority_css_class(self):
        """Get CSS class for priority styling."""
        priority_classes = {
            'low': 'text-success',
            'medium': 'text-warning',
            'high': 'text-danger',
            'critical': 'text-danger fw-bold'
        }
        return priority_classes.get(self.priority, 'text-secondary')
    
    @property
    def status_css_class(self):
        """Get CSS class for status styling."""
        status_classes = {
            'open': 'badge bg-primary',
            'in_progress': 'badge bg-warning',
            'resolved': 'badge bg-success',
            'closed': 'badge bg-secondary'
        }
        return status_classes.get(self.status, 'badge bg-secondary')
