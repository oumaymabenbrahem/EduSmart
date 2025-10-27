# -*- coding: utf-8 -*-
from django import forms
from django.db import models
from .models import Reclamation, CommentaireReclamation, TypeReclamation, ReponseAdministrateur


class ReclamationForm(forms.ModelForm):
    """Formulaire de création de réclamation"""

    class Meta:
        model = Reclamation
        fields = [
            'titre',
            'type_reclamation',
            'description',
            'priorite',
            'url_probleme',
            'fichier_joint',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre réclamation'
            }),
            'type_reclamation': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez en détail votre problème ou réclamation...'
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-select'
            }),
            'url_probleme': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL de la page où le problème s\'est produit (optionnel)'
            }),
            'fichier_joint': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer seulement les types actifs
        self.fields['type_reclamation'].queryset = TypeReclamation.objects.filter(is_active=True)
        
        # Rendre certains champs obligatoires
        self.fields['titre'].required = True
        self.fields['description'].required = True
        self.fields['type_reclamation'].required = True


class ReclamationAdminForm(forms.ModelForm):
    """Formulaire administrateur pour modifier une réclamation"""

    class Meta:
        model = Reclamation
        fields = [
            'titre',
            'type_reclamation',
            'description',
            'priorite',
            'statut',
            'assigne_a',
            'url_probleme',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'type_reclamation': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-select'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigne_a': forms.Select(attrs={
                'class': 'form-select'
            }),
            'url_probleme': forms.URLInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les utilisateurs qui peuvent être assignés (staff ou admin)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigne_a'].queryset = User.objects.filter(
            models.Q(is_staff=True) | models.Q(user_type__in=['admin', 'teacher'])
        ).distinct()


class CommentaireForm(forms.ModelForm):
    """Formulaire pour ajouter un commentaire à une réclamation"""

    class Meta:
        model = CommentaireReclamation
        fields = ['contenu', 'fichier_joint']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre commentaire ou réponse...'
            }),
            'fichier_joint': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenu'].required = True


class CommentaireAdminForm(forms.ModelForm):
    """Formulaire administrateur pour les commentaires"""

    class Meta:
        model = CommentaireReclamation
        fields = ['contenu', 'fichier_joint', 'is_internal']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre réponse...'
            }),
            'fichier_joint': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ReclamationSearchForm(forms.Form):
    """Formulaire de recherche et filtrage des réclamations"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par titre ou description...'
        })
    )
    
    type_reclamation = forms.ModelChoiceField(
        queryset=TypeReclamation.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les types",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Reclamation.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    priorite = forms.ChoiceField(
        choices=[('', 'Toutes les priorités')] + Reclamation.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class ReponseAdministrateurForm(forms.ModelForm):
    """Formulaire pour créer/modifier une réponse administrateur"""

    class Meta:
        model = ReponseAdministrateur
        fields = [
            'titre',
            'contenu',
            'statut',
            'fichier_joint',
            'notifier_utilisateur',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre réponse officielle'
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Rédigez votre réponse détaillée à la réclamation...'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fichier_joint': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
            }),
            'notifier_utilisateur': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titre'].required = True
        self.fields['contenu'].required = True
        
        # Personnaliser les choix de statut pour l'interface admin
        self.fields['statut'].choices = [
            ('brouillon', 'Brouillon (non visible par l\'utilisateur)'),
            ('publiee', 'Publier (visible par l\'utilisateur)'),
        ]


class ReponseAdministrateurQuickForm(forms.ModelForm):
    """Formulaire rapide pour répondre depuis le dashboard"""

    class Meta:
        model = ReponseAdministrateur
        fields = ['contenu', 'notifier_utilisateur']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Réponse rapide à la réclamation...'
            }),
            'notifier_utilisateur': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contenu'].required = True
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Publier automatiquement les réponses rapides
        instance.statut = 'publiee'
        if commit:
            instance.save()
        return instance
