from django import forms
from .models import Poll, PollOption


class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['question']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Which programming language do you prefer?',
                'maxlength': '500'
            })
        }

    def clean_question(self):
        question = self.cleaned_data.get('question', '').strip()
        if not question:
            raise forms.ValidationError("Poll question cannot be empty.")
        return question
