from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.urls import reverse

User = get_user_model()


class Poll(models.Model):
    """Model for polls that staff can create for team voting."""
    
    title = models.CharField(
        max_length=200, 
        verbose_name="Titel",
        help_text="Titel van de poll"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Beschrijving",
        help_text="Optionele beschrijving van de poll"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="created_polls",
        verbose_name="Aangemaakt door"
    )
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Aangemaakt op"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Actief",
        help_text="Actieve polls zijn zichtbaar en kunnen votes ontvangen"
    )
    allow_multiple_choices = models.BooleanField(
        default=False, 
        verbose_name="Meerdere antwoorden toestaan",
        help_text="Kunnen spelers meerdere opties selecteren?"
    )
    end_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Einddatum",
        help_text="Optionele einddatum waarop de poll automatisch sluit"
    )
    closed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Gesloten op"
    )
    closed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="closed_polls",
        verbose_name="Gesloten door"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Poll"
        verbose_name_plural = "Polls"

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        """Check if poll is open for voting."""
        if not self.is_active:
            return False
        if self.closed_at:
            return False
        if self.end_date and self.end_date <= timezone.now():
            return False
        return True

    @property
    def total_votes(self):
        """Get total number of votes cast."""
        return Vote.objects.filter(poll_option__poll=self).count()

    @property
    def unique_voters(self):
        """Get number of unique users who voted."""
        return Vote.objects.filter(poll_option__poll=self).values('user').distinct().count()

    def get_absolute_url(self):
        return reverse("polls:detail", kwargs={"pk": self.pk})

    def get_results(self):
        """Get poll results with vote counts for each option."""
        results = []
        unique_voters = self.unique_voters
        
        for option in self.options.all():
            vote_count = option.votes.count()
            percentage = (vote_count / unique_voters * 100) if unique_voters > 0 else 0
            results.append({
                'option': option,
                'vote_count': vote_count,
                'percentage': round(percentage, 1)
            })
        
        return results

    def close_poll(self, user=None):
        """Close the poll."""
        self.is_active = False
        self.closed_at = timezone.now()
        if user:
            self.closed_by = user
        self.save()


class PollOption(models.Model):
    """Model for poll options that users can vote for."""
    
    poll = models.ForeignKey(
        Poll, 
        on_delete=models.CASCADE, 
        related_name="options",
        verbose_name="Poll"
    )
    text = models.CharField(
        max_length=200, 
        verbose_name="Optie tekst"
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name="Volgorde",
        help_text="Volgorde waarin de optie wordt getoond"
    )

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Poll Optie"
        verbose_name_plural = "Poll Opties"

    def __str__(self):
        return f"{self.poll.title} - {self.text}"

    @property
    def vote_count(self):
        """Get number of votes for this option."""
        return self.votes.count()


class Vote(models.Model):
    """Model for individual votes on poll options."""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="poll_votes",
        verbose_name="Gebruiker"
    )
    poll_option = models.ForeignKey(
        PollOption, 
        on_delete=models.CASCADE, 
        related_name="votes",
        verbose_name="Poll optie"
    )
    voted_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Gestemd op"
    )

    class Meta:
        unique_together = ["user", "poll_option"]
        verbose_name = "Stem"
        verbose_name_plural = "Stemmen"

    def __str__(self):
        return f"{self.user} -> {self.poll_option.text}"

    @property
    def poll(self):
        """Get the poll this vote belongs to."""
        return self.poll_option.poll
