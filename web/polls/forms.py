from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Poll, PollOption


class PollForm(forms.ModelForm):
    """Form for creating and editing polls"""
    
    class Meta:
        model = Poll
        fields = [
            'title', 
            'description', 
            'allow_multiple_choices', 
            'end_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Voer de poll titel in...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optionele beschrijving van de poll...'
            }),
            'allow_multiple_choices': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set help texts in Dutch
        self.fields['title'].help_text = 'Titel van de poll'
        self.fields['description'].help_text = 'Optionele beschrijving'
        self.fields['allow_multiple_choices'].help_text = 'Kunnen spelers meerdere opties kiezen?'
        self.fields['end_date'].help_text = 'Optionele einddatum (laat leeg voor handmatig sluiten)'

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if end_date and end_date <= timezone.now():
            raise forms.ValidationError('Einddatum moet in de toekomst liggen.')
        return end_date


class PollOptionForm(forms.ModelForm):
    """Form for poll options"""
    
    class Meta:
        model = PollOption
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Voer optie tekst in...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].help_text = 'Tekst voor deze poll optie'


# Formset for managing multiple poll options
PollOptionFormSet = inlineformset_factory(
    Poll,
    PollOption,
    form=PollOptionForm,
    extra=3,  # Show 3 empty forms by default
    min_num=2,  # Require at least 2 options
    validate_min=True,
    can_delete=True,
    fields=['text']
)


class VoteForm(forms.Form):
    """Form for voting on polls"""
    
    def __init__(self, poll, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.poll = poll
        
        # Create choice field based on poll settings
        choices = [(option.id, option.text) for option in poll.options.all()]
        
        if poll.allow_multiple_choices:
            self.fields['options'] = forms.MultipleChoiceField(
                choices=choices,
                widget=forms.CheckboxSelectMultiple(attrs={
                    'class': 'form-check-input'
                }),
                label='Kies opties'
            )
        else:
            self.fields['options'] = forms.ChoiceField(
                choices=[('', '--- Kies een optie ---')] + choices,
                widget=forms.RadioSelect(attrs={
                    'class': 'form-check-input'
                }),
                label='Kies optie'
            )

    def clean_options(self):
        options = self.cleaned_data.get('options')
        
        if not options:
            raise forms.ValidationError('Je moet minimaal één optie selecteren.')
        
        # Validate option IDs belong to this poll
        if self.poll.allow_multiple_choices:
            valid_option_ids = set(
                str(option_id) for option_id in 
                self.poll.options.values_list('id', flat=True)
            )
            if not set(options).issubset(valid_option_ids):
                raise forms.ValidationError('Ongeldige opties geselecteerd.')
        else:
            if options not in [str(option_id) for option_id in self.poll.options.values_list('id', flat=True)]:
                raise forms.ValidationError('Ongeldige optie geselecteerd.')
        
        return options