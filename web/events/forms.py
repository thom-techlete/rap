from datetime import date, timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Event, MatchStatistic

User = get_user_model()


class EventForm(forms.ModelForm):
    # Additional fields for recurring events
    recurrence_type = forms.ChoiceField(
        choices=Event.RECURRENCE_TYPES,
        initial="none",
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Herhaling",
        help_text="Selecteer hoe vaak dit evenement herhaald moet worden",
    )

    recurrence_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
                "min": date.today().strftime("%Y-%m-%d"),
            }
        ),
        label="Einddatum herhaling",
        help_text="Tot welke datum moet het evenement herhaald worden?",
    )

    class Meta:
        model = Event
        fields = [
            "name",
            "description",
            "event_type",
            "date",
            "location",
            "max_participants",
            "is_mandatory",
        ]
        widgets = {
            "date": forms.DateTimeInput(
                attrs={
                    "type": "text",
                    "class": "form-control",
                    "placeholder": "dd/mm/jjjj uu:mm",
                    "autocomplete": "off",
                },
                format="%d/%m/%Y %H:%M",
            ),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "max_participants": forms.NumberInput(attrs={"class": "form-control"}),
            "event_type": forms.Select(attrs={"class": "form-select"}),
            "is_mandatory": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": "Naam",
            "description": "Beschrijving",
            "event_type": "Type evenement",
            "date": "Datum en tijd",
            "location": "Locatie",
            "max_participants": "Maximaal aantal deelnemers",
            "is_mandatory": "Verplichte aanwezigheid",
        }
        help_texts = {
            "date": "Vul in: dd/mm/jjjj uu:mm (bijvoorbeeld: 25/12/2024 14:30)",
            "max_participants": "Laat leeg voor onbeperkt aantal deelnemers",
            "is_mandatory": "Aanvinken als aanwezigheid verplicht is voor alle teamleden",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Format datetime for display in dd/mm/yyyy hh:mm format
        if self.instance and self.instance.pk and self.instance.date:
            # Convert to local timezone before formatting
            local_date = timezone.localtime(self.instance.date)
            self.initial["date"] = local_date.strftime("%d/%m/%Y %H:%M")
            # Set recurring fields if editing an existing recurring event
            if self.instance.is_recurring:
                self.initial["recurrence_type"] = self.instance.recurrence_type
                self.initial["recurrence_end_date"] = self.instance.recurrence_end_date

        # Set default end date to 3 months from now for new events
        if not self.instance.pk:
            self.initial["recurrence_end_date"] = date.today() + timedelta(days=90)

    def clean_date(self):
        """Convert the date from local timezone to UTC for storage"""
        date_value = self.cleaned_data.get("date")
        if date_value:
            # If the date is naive (no timezone info), treat it as local time
            if timezone.is_naive(date_value):
                # Convert from local timezone to UTC
                date_value = timezone.make_aware(date_value)
        return date_value

    def clean(self):
        cleaned_data = super().clean()
        recurrence_type = cleaned_data.get("recurrence_type")
        recurrence_end_date = cleaned_data.get("recurrence_end_date")
        event_date = cleaned_data.get("date")

        # If recurrence is enabled, end date is required
        if recurrence_type and recurrence_type != "none":
            if not recurrence_end_date:
                raise forms.ValidationError(
                    "Einddatum is verplicht voor herhalende evenementen."
                )

            # End date must be after event date
            if event_date and recurrence_end_date <= event_date.date():
                raise forms.ValidationError(
                    "Einddatum moet na de eerste evenementdatum liggen."
                )

        return cleaned_data


class MatchStatisticForm(forms.ModelForm):
    """Form for adding/editing match statistics"""
    
    class Meta:
        model = MatchStatistic
        fields = ['player', 'statistic_type', 'value', 'minute', 'notes']
        widgets = {
            'player': forms.Select(attrs={'class': 'form-select'}),
            'statistic_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'minute': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '120'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'player': 'Speler',
            'statistic_type': 'Type statistiek',
            'value': 'Aantal',
            'minute': 'Minuut',
            'notes': 'Opmerkingen',
        }
        help_texts = {
            'value': 'Aantal voor deze statistiek (standaard: 1)',
            'minute': 'In welke minuut van de wedstrijd (optioneel)',
            'notes': 'Extra informatie (optioneel)',
        }

    def __init__(self, *args, **kwargs):
        # Extract event from kwargs to filter players
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        # Filter players to only active users
        self.fields['player'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Update player display to show full name when available
        self.fields['player'].label_from_instance = lambda obj: (
            f"{obj.first_name} {obj.last_name}" if obj.first_name and obj.last_name else obj.username
        )

    def clean(self):
        cleaned_data = super().clean()
        if hasattr(self, 'instance') and self.instance and hasattr(self.instance, 'event') and self.instance.event:
            # Validate that this is a match event
            if not self.instance.event.is_match:
                raise forms.ValidationError("Statistieken kunnen alleen worden toegevoegd aan wedstrijden.")
        elif self.event:
            # Validate that this is a match event
            if not self.event.is_match:
                raise forms.ValidationError("Statistieken kunnen alleen worden toegevoegd aan wedstrijden.")
        
        return cleaned_data
