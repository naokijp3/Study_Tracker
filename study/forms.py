# study/forms.py

from django import forms
from .models import StudyLog, Category, StudyGoal

class StudyLogForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = StudyLog
        fields = ['category']

class StudyGoalForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = StudyGoal
        fields = ['category', 'target_minutes']