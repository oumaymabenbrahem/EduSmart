from django import forms
from .models import Topic, Post, Comment, Report


class TopicForm(forms.ModelForm):
    """Formulaire de création/édition de sujet"""
    
    class Meta:
        model = Topic
        fields = ['title', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre sujet',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Décrivez votre question ou sujet de discussion...',
                'required': True
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'python, django, web (séparés par des virgules)',
            }),
        }
        labels = {
            'title': 'Titre du sujet',
            'content': 'Contenu',
            'tags': 'Tags',
        }


class PostForm(forms.ModelForm):
    """Formulaire de réponse à un sujet"""
    
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Écrivez votre réponse...',
                'required': True
            }),
        }
        labels = {
            'content': 'Votre réponse',
        }


class CommentForm(forms.ModelForm):
    """Formulaire de commentaire sur un post"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ajouter un commentaire...',
                'required': True
            }),
        }
        labels = {
            'content': '',
        }


class ReportForm(forms.ModelForm):
    """Formulaire de signalement"""
    
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le problème (optionnel)...',
            }),
        }
        labels = {
            'reason': 'Raison du signalement',
            'description': 'Description',
        }


class SearchForm(forms.Form):
    """Formulaire de recherche dans le forum"""
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans le forum...',
        }),
        label=''
    )
    category = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Catégorie'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        categories = [('', 'Toutes les catégories')] + [
            (cat.id, cat.name) for cat in Category.objects.filter(is_active=True)
        ]
        self.fields['category'].choices = categories
