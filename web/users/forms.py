import os

try:
    import magic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import formset_factory

from .models import InvitationCode, Player


def validate_image_file(file):
    """Enhanced image file validation"""
    if not file:
        return

    # Check file size (5MB max)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("De foto mag maximaal 5MB zijn.")

    # Check file extension
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    _, ext = os.path.splitext(file.name.lower())
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Alleen {', '.join(allowed_extensions)} bestanden zijn toegestaan."
        )

    # Check MIME type using python-magic if available (more secure than relying on content_type)
    if HAS_MAGIC:
        try:
            file_mime = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)  # Reset file pointer

            allowed_mimes = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if file_mime not in allowed_mimes:
                raise ValidationError("Het bestand is geen geldige afbeelding.")
        except Exception:
            # Fallback to content_type if python-magic fails
            if hasattr(file, "content_type") and not file.content_type.startswith(
                "image/"
            ):
                print("geen geldige afbeelding")
    else:
        # Fallback to content_type if python-magic is not available
        if hasattr(file, "content_type") and not file.content_type.startswith("image/"):
            raise ValidationError("Het bestand is geen geldige afbeelding.")

    # Check for potential malicious content
    file.seek(0)
    content = file.read(1024)
    file.seek(0)

    # Look for common script tags or suspicious content
    suspicious_patterns = [b"<script", b"<?php", b"<%", b"javascript:", b"vbscript:"]
    content_lower = content.lower()

    for pattern in suspicious_patterns:
        if pattern in content_lower:
            raise ValidationError("Het bestand bevat verdachte inhoud.")


class PlayerProfileForm(forms.ModelForm):
    """Form for users to edit their own profile"""

    class Meta:
        model = Player
        fields = [
            "first_name",
            "last_name",
            "email",
            "telefoonnummer",
            "geboortedatum",
            "straat",
            "huisnummer",
            "toevoeging",
            "postcode",
            "plaats",
            "foto",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Je voornaam"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Je achternaam"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "je@email.com"}
            ),
            "telefoonnummer": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+31 6 12345678"}
            ),
            "geboortedatum": forms.DateInput(
                attrs={
                    "class": "form-control datepicker",
                    "placeholder": "dd/mm/jjjj",
                    "type": "text",
                    "autocomplete": "off",
                },
                format="%d/%m/%Y",
            ),
            "straat": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Straatnaam"}
            ),
            "huisnummer": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Huisnummer"}
            ),
            "toevoeging": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "1, HS, etc."}
            ),
            "postcode": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "1234 AB"}
            ),
            "plaats": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Plaatsnaam"}
            ),
            "foto": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }
        labels = {
            "first_name": "Voornaam",
            "last_name": "Achternaam",
            "email": "E-mailadres",
            "telefoonnummer": "Telefoonnummer",
            "geboortedatum": "Geboortedatum",
            "straat": "Straat",
            "huisnummer": "Huisnummer",
            "toevoeging": "Toevoeging",
            "postcode": "Postcode",
            "plaats": "Plaats",
            "foto": "Profielfoto",
        }
        help_texts = {
            "foto": "Upload een profielfoto (JPG, PNG). Maximaal 5MB.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Format the birth date for display in dd/mm/yyyy format
        if self.instance and self.instance.pk and self.instance.geboortedatum:
            self.initial["geboortedatum"] = self.instance.geboortedatum.strftime(
                "%d/%m/%Y"
            )

    def clean_foto(self):
        """Enhanced photo validation with security checks"""
        foto = self.cleaned_data.get("foto")
        if foto:
            # Validate uploaded photo with enhanced security
            validate_image_file(foto)
            # Additional checks can be added here
        return foto


class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form that provides specific error messages for inactive accounts"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Voer je gebruikersnaam in"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Voer je wachtwoord in"}
        )

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            # Check if user exists
            try:
                user = Player.objects.get(username=username)
                # Check if password is correct
                if user.check_password(password):
                    # Password is correct, but check if account is active
                    if not user.is_active:
                        raise ValidationError(
                            "Je account is nog niet geactiveerd door een beheerder. "
                            "Neem contact op met een teamlid of wacht tot je account wordt geactiveerd.",
                            code="inactive",
                        )
                    # If we get here, account is active, proceed with normal authentication
                    self.user_cache = authenticate(
                        self.request, username=username, password=password
                    )
                    if self.user_cache is None:
                        raise ValidationError(
                            self.error_messages["invalid_login"],
                            code="invalid_login",
                            params={"username": self.username_field.verbose_name},
                        )
                else:
                    # Password is incorrect
                    raise ValidationError(
                        self.error_messages["invalid_login"],
                        code="invalid_login",
                        params={"username": self.username_field.verbose_name},
                    )
            except Player.DoesNotExist:
                # User doesn't exist
                raise ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                ) from None

        return self.cleaned_data


class InvitationCodeRegistrationForm(UserCreationForm):
    """Custom registration form that requires an invitation code"""

    invitation_code = forms.CharField(
        max_length=50,
        required=True,
        label="Uitnodigingscode",
        help_text="Voer de uitnodigingscode in die je hebt ontvangen",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Voer je uitnodigingscode in",
                "class": "form-control",
            }
        ),
    )

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Voornaam",
        widget=forms.TextInput(
            attrs={"placeholder": "Je voornaam", "class": "form-control"}
        ),
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Achternaam",
        widget=forms.TextInput(
            attrs={"placeholder": "Je achternaam", "class": "form-control"}
        ),
    )

    email = forms.EmailField(
        required=True,
        label="E-mailadres",
        widget=forms.EmailInput(
            attrs={"placeholder": "je@email.com", "class": "form-control"}
        ),
    )

    class Meta:
        model = Player
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "invitation_code",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to default fields
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Kies een gebruikersnaam"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Maak een sterk wachtwoord"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Herhaal je wachtwoord"}
        )

    def clean_invitation_code(self):
        """Validate the invitation code"""
        code = self.cleaned_data.get("invitation_code")
        if not code:
            raise ValidationError("Uitnodigingscode is verplicht.")

        try:
            invitation = InvitationCode.objects.get(code=code)
        except InvitationCode.DoesNotExist:
            raise ValidationError(
                "Ongeldige uitnodigingscode. Controleer de code en probeer het opnieuw."
            ) from None

        is_valid, error_message = invitation.is_valid()
        if not is_valid:
            raise ValidationError(error_message)

        return code

    def save(self, commit=True):
        """Save the user and mark the invitation code as used"""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.is_active = False  # Require admin activation

        if commit:
            # Get invitation code to set user_type
            invitation_code = self.cleaned_data["invitation_code"]
            invitation = InvitationCode.objects.get(code=invitation_code)
            user.user_type = invitation.user_type  # Set user type based on invitation
            user.save()
            # Mark invitation code as used
            invitation.use_code()

        return user


class PlayerPositionRugnummerForm(forms.ModelForm):
    """Form for editing a single player's position and jersey number"""

    class Meta:
        model = Player
        fields = ["positie", "rugnummer"]
        widgets = {
            "positie": forms.Select(
                choices=[
                    ("", "Geen positie"),
                    ("Keeper", "Keeper"),
                    ("Verdediger", "Verdediger"),
                    ("Middenvelder", "Middenvelder"),
                    ("Aanvaller", "Aanvaller"),
                    ("Vleugelspeler", "Vleugelspeler"),
                    ("Centrale verdediger", "Centrale verdediger"),
                    ("Linksback", "Linksback"),
                    ("Rechtsback", "Rechtsback"),
                    ("Defensieve middenvelder", "Defensieve middenvelder"),
                    ("Centrale middenvelder", "Centrale middenvelder"),
                    ("Aanvallende middenvelder", "Aanvallende middenvelder"),
                    ("Linkervleugel", "Linkervleugel"),
                    ("Rechtervleugel", "Rechtervleugel"),
                    ("Spits", "Spits"),
                ],
                attrs={"class": "form-select form-select-sm"},
            ),
            "rugnummer": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "min": "1",
                    "max": "99",
                    "placeholder": "#",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["positie"].required = False
        self.fields["rugnummer"].required = False

    def clean_rugnummer(self):
        """Validate that jersey number is unique (if provided)"""
        rugnummer = self.cleaned_data.get("rugnummer")
        if rugnummer:
            # Check if another player already has this number
            existing_player = (
                Player.objects.filter(rugnummer=rugnummer)
                .exclude(pk=self.instance.pk if self.instance else None)
                .first()
            )

            if existing_player:
                raise ValidationError(
                    f"Rugnummer {rugnummer} is al in gebruik door {existing_player.get_full_name()}."
                )

        return rugnummer


# Create a formset for bulk editing multiple players
PlayerPositionRugnummerFormSet = formset_factory(
    PlayerPositionRugnummerForm,
    extra=0,  # Don't show extra empty forms
    can_delete=False,
)
