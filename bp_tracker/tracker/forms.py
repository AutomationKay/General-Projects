# tracker/forms.py
from django import forms 
from .models import Reading

class ReadingForm(forms.ModelForm):
    class Meta:
        model = Reading
        fields = ['systolic', 'diastolic', 'pulse']

