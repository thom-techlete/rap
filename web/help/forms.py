from django import forms
from .models import BugReport


class BugReportForm(forms.ModelForm):
    """Form for users to submit bug reports."""
    
    class Meta:
        model = BugReport
        fields = [
            'title',
            'description', 
            'steps_to_reproduce',
            'expected_behavior',
            'actual_behavior',
            'browser_info'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Korte beschrijving van het probleem'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Beschrijf het probleem dat je hebt ondervonden...'
            }),
            'steps_to_reproduce': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Bijv. 1. Ga naar pagina X, 2. Klik op knop Y, 3. ...'
            }),
            'expected_behavior': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Wat had er moeten gebeuren?'
            }),
            'actual_behavior': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Wat gebeurde er daadwerkelijk?'
            }),
            'browser_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bijv. Chrome 91, Safari 14, Firefox 89'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields
        self.fields['title'].required = True
        self.fields['description'].required = True
        
        # Add help text
        self.fields['browser_info'].help_text = "Optioneel: welke browser en versie gebruik je?"


class AdminBugReportForm(forms.ModelForm):
    """Form for admins to manage bug reports."""
    
    class Meta:
        model = BugReport
        fields = [
            'status',
            'priority',
            'assigned_to',
            'admin_notes'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Interne notities voor het ontwikkelteam...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff users for assignment
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        self.fields['assigned_to'].empty_label = "Niet toegewezen"