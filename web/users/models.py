import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class InvitationCode(models.Model):
    """Model for invitation codes that allow users to register"""

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Uitnodigingscode",
        help_text="Unieke code die gebruikers kunnen gebruiken om te registreren",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Beschrijving",
        help_text="Beschrijving van waarvoor deze code is (bijv. 'Nieuwe spelers 2025')",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actief",
        help_text="Alleen actieve codes kunnen gebruikt worden voor registratie",
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Maximaal aantal gebruiken",
        help_text="Laat leeg voor onbeperkt gebruik",
    )
    used_count = models.PositiveIntegerField(
        default=0, verbose_name="Aantal keer gebruikt"
    )
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name="Aangemaakt op"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Verloopt op",
        help_text="Laat leeg als de code niet verloopt",
    )
    created_by = models.ForeignKey(
        "Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Aangemaakt door",
    )

    class Meta:
        verbose_name = "Uitnodigingscode"
        verbose_name_plural = "Uitnodigingscodes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.description})" if self.description else self.code

    def save(self, *args, **kwargs):
        if not self.code:
            # Generate a unique code if none provided
            self.code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if the invitation code is valid for use"""
        if not self.is_active:
            return False, "Deze uitnodigingscode is niet meer actief."

        if self.expires_at and self.expires_at < timezone.now():
            return False, "Deze uitnodigingscode is verlopen."

        if self.max_uses and self.used_count >= self.max_uses:
            return (
                False,
                "Deze uitnodigingscode heeft het maximaal aantal gebruiken bereikt.",
            )

        return True, ""

    def use_code(self):
        """Increment the used count"""
        self.used_count += 1
        self.save()


class Player(AbstractUser):
    # Extra player info fields
    geboortedatum = models.DateField(
        null=True, blank=True, verbose_name="Geboortedatum"
    )
    telefoonnummer = models.CharField(
        max_length=20, blank=True, verbose_name="Telefoonnummer"
    )
    positie = models.CharField(max_length=50, blank=True, verbose_name="Positie")
    rugnummer = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Rugnummer"
    )
    straat = models.CharField(max_length=100, blank=True, verbose_name="Straat")
    huisnummer = models.CharField(max_length=10, blank=True, verbose_name="Huisnummer")
    toevoeging = models.CharField(max_length=10, blank=True, verbose_name="Toevoeging")
    postcode = models.CharField(max_length=10, blank=True, verbose_name="Postcode")
    plaats = models.CharField(max_length=50, blank=True, verbose_name="Plaats")
    adres = models.CharField(
        max_length=255, blank=True, verbose_name="Adres"
    )  # Keep for backward compatibility
    foto = models.ImageField(
        upload_to="profile_pics/",
        null=True,
        blank=True,
        verbose_name="Profielfoto",
    )

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

    @property
    def full_address(self):
        """Construct full address from separate fields"""
        parts = []
        if self.straat:
            street_part = self.straat
            if self.huisnummer:
                street_part += f" {self.huisnummer}"
                if self.toevoeging:
                    street_part += f" {self.toevoeging}"
            parts.append(street_part)

        if self.postcode and self.plaats:
            parts.append(f"{self.postcode} {self.plaats}")
        elif self.plaats:
            parts.append(self.plaats)

        return ", ".join(parts) if parts else ""
