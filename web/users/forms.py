from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import InvitationCode, Player


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
                    "class": "form-control",
                    "placeholder": "dd/mm/jjjj",
                    "type": "text",
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
            "geboortedatum": "Formaat: dd/mm/jjjj (bijvoorbeeld 15/03/1990)",
            "telefoonnummer": "Optioneel - voor contact bij evenementen",
            "toevoeging": "Optioneel - bijvoorbeeld A, bis, 1 hoog",
            "postcode": "Bijvoorbeeld: 1234 AB",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Format the birth date for display in dd/mm/yyyy format
        if self.instance and self.instance.pk and self.instance.geboortedatum:
            self.initial["geboortedatum"] = self.instance.geboortedatum.strftime(
                "%d/%m/%Y"
            )

    def clean_foto(self):
        """Validate uploaded photo"""
        foto = self.cleaned_data.get("foto")
        if foto:
            # Only validate if it's a new uploaded file (has content_type attribute)
            # If it's an existing ImageFieldFile, skip validation
            if hasattr(foto, "content_type"):
                # Check file size (5MB max)
                if foto.size > 5 * 1024 * 1024:
                    raise ValidationError("De foto mag maximaal 5MB zijn.")

                # Check file type
                if not foto.content_type.startswith("image/"):
                    raise ValidationError(
                        "Upload alleen afbeeldingsbestanden (JPG, PNG, etc.)."
                    )

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
            user.save()
            # Mark invitation code as used
            invitation_code = self.cleaned_data["invitation_code"]
            invitation = InvitationCode.objects.get(code=invitation_code)
            invitation.use_code()

        return user
