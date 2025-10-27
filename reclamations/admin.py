# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.html import format_html
from .models import TypeReclamation, Reclamation, CommentaireReclamation, SuiviReclamation, ReponseAdministrateur


@admin.register(TypeReclamation)
class TypeReclamationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'colored_icon', 'is_active', 'created_at']
    list_filter = ['is_active', 'code']
    search_fields = ['name', 'description']
    ordering = ['name']

    def colored_icon(self, obj):
        return format_html(
            '<i class="{}" style="color: {}; font-size: 1.2em;"></i>',
            obj.icon,
            obj.color
        )
    colored_icon.short_description = 'Icône'


class CommentaireInline(admin.TabularInline):
    model = CommentaireReclamation
    extra = 0
    readonly_fields = ['created_at']
    fields = ['auteur', 'contenu', 'is_internal', 'created_at']


class SuiviInline(admin.TabularInline):
    model = SuiviReclamation
    extra = 0
    readonly_fields = ['created_at']
    fields = ['ancien_statut', 'nouveau_statut', 'modifie_par', 'commentaire', 'created_at']


class ReponseAdminInline(admin.TabularInline):
    model = ReponseAdministrateur
    extra = 0
    readonly_fields = ['created_at', 'date_publication', 'date_lecture']
    fields = ['titre', 'contenu', 'statut', 'notifier_utilisateur', 'lu_par_utilisateur', 'created_at']


@admin.register(Reclamation)
class ReclamationAdmin(admin.ModelAdmin):
    list_display = [
        'titre', 'utilisateur', 'type_reclamation', 'colored_priorite', 
        'colored_statut', 'assigne_a', 'is_overdue_display', 'created_at'
    ]
    list_filter = [
        'statut', 'priorite', 'type_reclamation', 'created_at', 
        'assigne_a', 'date_resolution'
    ]
    search_fields = ['titre', 'description', 'utilisateur__username']
    readonly_fields = ['created_at', 'updated_at', 'date_resolution']
    ordering = ['-created_at']
    inlines = [CommentaireInline, SuiviInline, ReponseAdminInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('titre', 'type_reclamation', 'description', 'utilisateur')
        }),
        ('Gestion', {
            'fields': ('priorite', 'statut', 'assigne_a')
        }),
        ('Détails techniques', {
            'fields': ('url_probleme', 'navigateur', 'systeme_exploitation', 'fichier_joint'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'date_resolution'),
            'classes': ('collapse',)
        }),
    )

    def colored_priorite(self, obj):
        return format_html(
            '<span class="badge" style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.priority_color,
            obj.get_priorite_display()
        )
    colored_priorite.short_description = 'Priorité'

    def colored_statut(self, obj):
        return format_html(
            '<span class="badge" style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.status_color,
            obj.get_statut_display()
        )
    colored_statut.short_description = 'Statut'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ En retard</span>'
            )
        return '✅ À jour'
    is_overdue_display.short_description = 'État'

    actions = ['marquer_en_cours', 'marquer_resolu', 'assigner_a_moi']

    def marquer_en_cours(self, request, queryset):
        count = 0
        for reclamation in queryset:
            if reclamation.statut != 'en_cours':
                ancien_statut = reclamation.statut
                reclamation.statut = 'en_cours'
                reclamation.save()
                
                SuiviReclamation.objects.create(
                    reclamation=reclamation,
                    ancien_statut=ancien_statut,
                    nouveau_statut='en_cours',
                    modifie_par=request.user,
                    commentaire=f"Marqué en cours par {request.user.username} (action groupée)"
                )
                count += 1
        
        self.message_user(request, f"{count} réclamation(s) marquée(s) en cours.")
    marquer_en_cours.short_description = "Marquer comme 'En cours'"

    def marquer_resolu(self, request, queryset):
        count = 0
        for reclamation in queryset:
            if reclamation.statut != 'resolue':
                ancien_statut = reclamation.statut
                reclamation.statut = 'resolue'
                reclamation.save()
                
                SuiviReclamation.objects.create(
                    reclamation=reclamation,
                    ancien_statut=ancien_statut,
                    nouveau_statut='resolue',
                    modifie_par=request.user,
                    commentaire=f"Marqué résolu par {request.user.username} (action groupée)"
                )
                count += 1
        
        self.message_user(request, f"{count} réclamation(s) marquée(s) comme résolue(s).")
    marquer_resolu.short_description = "Marquer comme 'Résolue'"

    def assigner_a_moi(self, request, queryset):
        count = queryset.update(assigne_a=request.user)
        self.message_user(request, f"{count} réclamation(s) assignée(s) à vous.")
    assigner_a_moi.short_description = "M'assigner ces réclamations"


@admin.register(CommentaireReclamation)
class CommentaireReclamationAdmin(admin.ModelAdmin):
    list_display = ['reclamation', 'auteur', 'contenu_court', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at', 'auteur']
    search_fields = ['contenu', 'reclamation__titre', 'auteur__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def contenu_court(self, obj):
        return obj.contenu[:50] + '...' if len(obj.contenu) > 50 else obj.contenu
    contenu_court.short_description = 'Contenu'


@admin.register(SuiviReclamation)
class SuiviReclamationAdmin(admin.ModelAdmin):
    list_display = ['reclamation', 'ancien_statut', 'nouveau_statut', 'modifie_par', 'created_at']
    list_filter = ['ancien_statut', 'nouveau_statut', 'created_at', 'modifie_par']
    search_fields = ['reclamation__titre', 'commentaire', 'modifie_par__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(ReponseAdministrateur)
class ReponseAdministrateurAdmin(admin.ModelAdmin):
    list_display = [
        'reclamation', 'titre', 'administrateur', 'colored_statut', 
        'lu_par_utilisateur', 'email_envoye', 'created_at'
    ]
    list_filter = [
        'statut', 'lu_par_utilisateur', 'email_envoye', 'notifier_utilisateur', 
        'created_at', 'administrateur'
    ]
    search_fields = ['titre', 'contenu', 'reclamation__titre', 'administrateur__username']
    readonly_fields = ['created_at', 'updated_at', 'date_publication', 'date_lecture', 'date_envoi_email']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('reclamation', 'administrateur', 'titre', 'contenu', 'fichier_joint')
        }),
        ('Publication', {
            'fields': ('statut', 'date_publication')
        }),
        ('Notification', {
            'fields': ('notifier_utilisateur', 'email_envoye', 'date_envoi_email'),
            'classes': ('collapse',)
        }),
        ('Lecture utilisateur', {
            'fields': ('lu_par_utilisateur', 'date_lecture'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def colored_statut(self, obj):
        colors = {
            'brouillon': '#6c757d',
            'publiee': '#28a745',
            'archivee': '#ffc107',
        }
        return format_html(
            '<span class="badge" style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.statut, '#6c757d'),
            obj.get_statut_display()
        )
    colored_statut.short_description = 'Statut'

    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau objet
            obj.administrateur = request.user
        super().save_model(request, obj, form, change)
