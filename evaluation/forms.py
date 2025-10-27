from django import forms
from django.forms import inlineformset_factory
from .models import Evaluation, Question


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['title', 'description', 'start_date', 'end_date', 'is_published']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'choices', 'correct_answer', 'points']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
            'choices': forms.Textarea(attrs={'rows': 3, 'placeholder': 'JSON list, e.g. ["A","B","C"]'}),
            'correct_answer': forms.Textarea(attrs={'rows': 2}),
        }


QuestionFormSet = inlineformset_factory(
    Evaluation,
    Question,
    form=QuestionForm,
    extra=3,
    can_delete=True,
    max_num=100,
)
