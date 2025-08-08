from django import forms

from .models import Event


class EventForm(forms.ModelForm):
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
            self.initial["date"] = self.instance.date.strftime("%d/%m/%Y %H:%M")
