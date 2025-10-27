from django import forms
from .models import Course, CourseModule, CourseResource


class CourseForm(forms.ModelForm):
    """Formulaire de création/modification de cours"""

    class Meta:
        model = Course
        fields = [
            'title',
            'subject',
            'level',
            'description',
            'objectives',
            'prerequisites',
            'content',
            'duration_hours',
            'thumbnail',
            'status',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du cours'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du cours'
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Objectifs d\'apprentissage'
            }),
            'prerequisites': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Prérequis nécessaires'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Contenu détaillé du cours'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1000,
                'placeholder': 'Durée en heures'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs obligatoires
        self.fields['title'].required = True
        self.fields['subject'].required = True
        self.fields['level'].required = True
        self.fields['description'].required = True
        self.fields['content'].required = True
        self.fields['duration_hours'].required = True

        # Rendre certains champs optionnels
        self.fields['objectives'].required = False
        self.fields['prerequisites'].required = False
        self.fields['thumbnail'].required = False


class SimpleCourseForm(forms.ModelForm):
    """Formulaire simplifié de création de cours"""

    class Meta:
        model = Course
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du cours'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du cours'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['description'].required = True


class CourseModuleForm(forms.ModelForm):
    """Formulaire pour créer/modifier un module de cours"""

    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'content_file', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du module'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du module'
            }),
            'content_file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Ordre d\'affichage'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['content_file'].required = True
        self.fields['description'].required = False
        self.fields['order'].required = False


class CourseResourceForm(forms.ModelForm):
    """Formulaire pour créer/modifier une ressource de cours"""

    class Meta:
        model = CourseResource
        fields = ['title', 'resource_type', 'description', 'file', 'url', 'module']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de la ressource'
            }),
            'resource_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la ressource'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'module': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['resource_type'].required = True
        self.fields['description'].required = False
        self.fields['file'].required = False
        self.fields['url'].required = False
        self.fields['module'].required = False

        if self.course:
            self.fields['module'].queryset = CourseModule.objects.filter(course=self.course, is_active=True)
