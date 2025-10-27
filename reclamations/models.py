# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


class TypeReclamation(models.Model):
    """Types de réclamations disponibles"""
    TYPES_CHOICES = [
        ('technique', 'Problème technique'),
        ('contenu', 'Problème de contenu'),
        ('acces', 'Problème d\'accès'),
        ('evaluation', 'Problème d\'évaluation'),
        ('forum', 'Problème de forum'),
        ('autre', 'Autre'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Nom du type')
    code = models.CharField(max_length=20, choices=TYPES_CHOICES, unique=True, verbose_name='Code')
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(max_length=50, default='bi-exclamation-triangle', help_text='Classe d\'icône Bootstrap')
    color = models.CharField(max_length=7, default='#ffc107', help_text='Couleur hexadécimale')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Type de réclamation'
        verbose_name_plural = 'Types de réclamations'
        ordering = ['name']

    def __str__(self):
        return self.name


class Reclamation(models.Model):
    """Modèle pour les réclamations des utilisateurs"""
    PRIORITY_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('en_cours', 'En cours de traitement'),
        ('en_attente', 'En attente de réponse'),
        ('resolue', 'Résolue'),
        ('fermee', 'Fermée'),
        ('rejetee', 'Rejetée'),
    ]

    # Informations de base
    titre = models.CharField(max_length=200, verbose_name='Titre de la réclamation')
    description = models.TextField(verbose_name='Description détaillée')
    type_reclamation = models.ForeignKey(TypeReclamation, on_delete=models.CASCADE, verbose_name='Type de réclamation')
    
    # Utilisateur
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Utilisateur')
    
    # Priorité et statut
    priorite = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normale', verbose_name='Priorité')
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ouverte', verbose_name='Statut')
    
    # Assignation
    assigne_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reclamations_assignees',
        verbose_name='Assigné à'
    )
    
    # Fichiers joints
    fichier_joint = models.FileField(
        upload_to='reclamations/fichiers/%Y/%m/', 
        blank=True, 
        null=True,
        verbose_name='Fichier joint'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    date_resolution = models.DateTimeField(null=True, blank=True, verbose_name='Date de résolution')
    
    # Informations supplémentaires
    url_probleme = models.URLField(blank=True, verbose_name='URL du problème')
    navigateur = models.CharField(max_length=100, blank=True, verbose_name='Navigateur')
    systeme_exploitation = models.CharField(max_length=100, blank=True, verbose_name='Système d\'exploitation')
    
    class Meta:
        verbose_name = 'Réclamation'
        verbose_name_plural = 'Réclamations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titre} - {self.utilisateur.username}"

    def get_absolute_url(self):
        return reverse('reclamations:detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Marquer la date de résolution si le statut change vers résolu
        if self.statut == 'resolue' and not self.date_resolution:
            self.date_resolution = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Vérifie si la réclamation est en retard (plus de 7 jours sans résolution)"""
        if self.statut in ['resolue', 'fermee']:
            return False
        return (timezone.now() - self.created_at).days > 7

    @property
    def priority_color(self):
        """Retourne la couleur associée à la priorité"""
        colors = {
            'basse': '#28a745',
            'normale': '#17a2b8',
            'haute': '#ffc107',
            'urgente': '#dc3545',
        }
        return colors.get(self.priorite, '#6c757d')

    @property
    def status_color(self):
        """Retourne la couleur associée au statut"""
        colors = {
            'ouverte': '#007bff',
            'en_cours': '#ffc107',
            'en_attente': '#fd7e14',
            'resolue': '#28a745',
            'fermee': '#6c757d',
            'rejetee': '#dc3545',
        }
        return colors.get(self.statut, '#6c757d')


class CommentaireReclamation(models.Model):
    """Commentaires et réponses aux réclamations"""
    reclamation = models.ForeignKey(Reclamation, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Auteur')
    contenu = models.TextField(verbose_name='Contenu du commentaire')
    fichier_joint = models.FileField(
        upload_to='reclamations/commentaires/%Y/%m/', 
        blank=True, 
        null=True,
        verbose_name='Fichier joint'
    )
    is_internal = models.BooleanField(default=False, verbose_name='Commentaire interne (non visible par l\'utilisateur)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')

    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire de {self.auteur.username} sur {self.reclamation.titre}"


class SuiviReclamation(models.Model):
    """Historique des changements de statut d'une réclamation"""
    reclamation = models.ForeignKey(Reclamation, on_delete=models.CASCADE, related_name='historique')
    ancien_statut = models.CharField(max_length=20, verbose_name='Ancien statut')
    nouveau_statut = models.CharField(max_length=20, verbose_name='Nouveau statut')
    modifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Modifié par')
    commentaire = models.TextField(blank=True, verbose_name='Commentaire sur le changement')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date du changement')

    class Meta:
        verbose_name = 'Suivi de réclamation'
        verbose_name_plural = 'Suivis de réclamations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reclamation.titre}: {self.ancien_statut} → {self.nouveau_statut}"


class ReponseAdministrateur(models.Model):
    """Réponses officielles des administrateurs aux réclamations"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publiee', 'Publiée'),
        ('archivee', 'Archivée'),
    ]
    
    reclamation = models.ForeignKey(Reclamation, on_delete=models.CASCADE, related_name='reponses_admin')
    administrateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Administrateur')
    titre = models.CharField(max_length=200, verbose_name='Titre de la réponse')
    contenu = models.TextField(verbose_name='Contenu de la réponse')
    
    # Statut de la réponse
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon', verbose_name='Statut')
    
    # Fichiers joints
    fichier_joint = models.FileField(
        upload_to='reclamations/reponses_admin/%Y/%m/', 
        blank=True, 
        null=True,
        verbose_name='Fichier joint'
    )
    
    # Notification à l'utilisateur
    notifier_utilisateur = models.BooleanField(default=True, verbose_name='Notifier l\'utilisateur par email')
    email_envoye = models.BooleanField(default=False, verbose_name='Email envoyé')
    date_envoi_email = models.DateTimeField(null=True, blank=True, verbose_name='Date d\'envoi de l\'email')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    date_publication = models.DateTimeField(null=True, blank=True, verbose_name='Date de publication')
    
    # Lecture par l'utilisateur
    lu_par_utilisateur = models.BooleanField(default=False, verbose_name='Lu par l\'utilisateur')
    date_lecture = models.DateTimeField(null=True, blank=True, verbose_name='Date de lecture')

    class Meta:
        verbose_name = 'Réponse administrateur'
        verbose_name_plural = 'Réponses administrateur'
        ordering = ['-created_at']

    def __str__(self):
        return f"Réponse à '{self.reclamation.titre}' par {self.administrateur.username}"

    def save(self, *args, **kwargs):
        # Marquer la date de publication si le statut change vers publié
        if self.statut == 'publiee' and not self.date_publication:
            self.date_publication = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        """Vérifie si la réponse est publiée"""
        return self.statut == 'publiee'

    @property
    def is_new_for_user(self):
        """Vérifie si la réponse est nouvelle pour l'utilisateur"""
        return self.is_published and not self.lu_par_utilisateur
