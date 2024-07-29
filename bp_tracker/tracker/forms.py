# tracker/forms.py
from django import forms
from .models import Reading
import pandas as pd
from pathlib import Path
from django.conf import settings

class ReadingForm(forms.ModelForm):
    """
    Form to log a new blood pressure reading.
    """
    sex = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])

    class Meta:
        model = Reading
        fields = ['systolic', 'diastolic', 'pulse', 'sex', 'country']
        widgets = {
            'country': forms.Select(choices=[]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load country choices from the dataset
        data_path = Path(settings.BASE_DIR) / 'data' / 'bp_standardised_cleaned.csv'
        data = pd.read_csv(data_path)
        countries = data['country'].unique()
        country_choices = [(country, country) for country in countries]
        self.fields['country'].widget.choices = country_choices