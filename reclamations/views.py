# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Reclamation, CommentaireReclamation, TypeReclamation, SuiviReclamation, ReponseAdministrateur
from .forms import ReclamationForm, ReclamationAdminForm, CommentaireForm, CommentaireAdminForm, ReclamationSearchForm, ReponseAdministrateurForm, ReponseAdministrateurQuickForm

User = get_user_model()


@login_required
def reclamation_list(request):
    """Liste des réclamations pour l'utilisateur connecté"""
    reclamations = Reclamation.objects.filter(utilisateur=request.user).order_by('-created_at')
    
    # Filtres
    form = ReclamationSearchForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['search']:
            reclamations = reclamations.filter(
                Q(titre__icontains=form.cleaned_data['search']) |
                Q(description__icontains=form.cleaned_data['search'])
            )
        if form.cleaned_data['type_reclamation']:
            reclamations = reclamations.filter(type_reclamation=form.cleaned_data['type_reclamation'])
        if form.cleaned_data['statut']:
            reclamations = reclamations.filter(statut=form.cleaned_data['statut'])
        if form.cleaned_data['priorite']:
            reclamations = reclamations.filter(priorite=form.cleaned_data['priorite'])
        if form.cleaned_data['date_debut']:
            reclamations = reclamations.filter(created_at__gte=form.cleaned_data['date_debut'])
        if form.cleaned_data['date_fin']:
            reclamations = reclamations.filter(created_at__lte=form.cleaned_data['date_fin'])

    # Statistiques avec réponses non lues
    from django.db.models import Exists, OuterRef
    
    # Sous-requête pour vérifier s'il y a des réponses non lues
    reponses_non_lues = ReponseAdministrateur.objects.filter(
        reclamation=OuterRef('pk'),
        statut='publiee',
        lu_par_utilisateur=False
    )
    
    # Annoter les réclamations avec l'information des réponses non lues
    reclamations = reclamations.annotate(
        has_unread_responses=Exists(reponses_non_lues)
    )
    
    # Pagination
    paginator = Paginator(reclamations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Compter les réponses non lues
    total_reponses_non_lues = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=request.user,
        statut='publiee',
        lu_par_utilisateur=False
    ).count()
    
    stats = {
        'total': reclamations.count(),
        'ouvertes': reclamations.filter(statut='ouverte').count(),
        'en_cours': reclamations.filter(statut='en_cours').count(),
        'resolues': reclamations.filter(statut='resolue').count(),
        'reponses_non_lues': total_reponses_non_lues,
    }

    context = {
        'page_obj': page_obj,
        'form': form,
        'stats': stats,
    }
    return render(request, 'reclamations/reclamation_list.html', context)


@login_required
def admin_reclamation_list(request):
    """Vue administrative de toutes les réclamations"""
    # Vérifier les permissions
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('accounts:dashboard')

    reclamations = Reclamation.objects.select_related('utilisateur', 'type_reclamation', 'assigne_a').order_by('-created_at')
    
    # Filtres
    form = ReclamationSearchForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['search']:
            reclamations = reclamations.filter(
                Q(titre__icontains=form.cleaned_data['search']) |
                Q(description__icontains=form.cleaned_data['search']) |
                Q(utilisateur__username__icontains=form.cleaned_data['search'])
            )
        if form.cleaned_data['type_reclamation']:
            reclamations = reclamations.filter(type_reclamation=form.cleaned_data['type_reclamation'])
        if form.cleaned_data['statut']:
            reclamations = reclamations.filter(statut=form.cleaned_data['statut'])
        if form.cleaned_data['priorite']:
            reclamations = reclamations.filter(priorite=form.cleaned_data['priorite'])
        if form.cleaned_data['date_debut']:
            reclamations = reclamations.filter(created_at__gte=form.cleaned_data['date_debut'])
        if form.cleaned_data['date_fin']:
            reclamations = reclamations.filter(created_at__lte=form.cleaned_data['date_fin'])

    # Filtres supplémentaires pour admin
    assigne_filter = request.GET.get('assigne')
    if assigne_filter == 'moi':
        reclamations = reclamations.filter(assigne_a=request.user)
    elif assigne_filter == 'non_assigne':
        reclamations = reclamations.filter(assigne_a__isnull=True)

    # Pagination
    paginator = Paginator(reclamations, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques globales
    stats = {
        'total': Reclamation.objects.count(),
        'ouvertes': Reclamation.objects.filter(statut='ouverte').count(),
        'en_cours': Reclamation.objects.filter(statut='en_cours').count(),
        'en_attente': Reclamation.objects.filter(statut='en_attente').count(),
        'resolues': Reclamation.objects.filter(statut='resolue').count(),
        'urgentes': Reclamation.objects.filter(priorite='urgente', statut__in=['ouverte', 'en_cours']).count(),
        'en_retard': sum(1 for r in Reclamation.objects.filter(statut__in=['ouverte', 'en_cours']) if r.is_overdue),
    }

    context = {
        'page_obj': page_obj,
        'form': form,
        'stats': stats,
        'assigne_filter': assigne_filter,
    }
    return render(request, 'reclamations/admin_dashboard_list.html', context)


@login_required
def reclamation_create(request):
    """Créer une nouvelle réclamation"""
    if request.method == 'POST':
        form = ReclamationForm(request.POST, request.FILES)
        if form.is_valid():
            reclamation = form.save(commit=False)
            reclamation.utilisateur = request.user
            
            # Capturer des informations sur le navigateur si disponibles
            if 'HTTP_USER_AGENT' in request.META:
                user_agent = request.META['HTTP_USER_AGENT']
                reclamation.navigateur = user_agent[:100]  # Limiter la longueur
            
            reclamation.save()
            
            messages.success(request, f"Votre réclamation '{reclamation.titre}' a été créée avec succès.")
            return redirect('reclamations:detail', pk=reclamation.pk)
    else:
        form = ReclamationForm()

    context = {
        'form': form,
        'types_reclamation': TypeReclamation.objects.filter(is_active=True),
    }
    return render(request, 'reclamations/reclamation_create.html', context)


@login_required
def reclamation_detail(request, pk):
    """Détail d'une réclamation"""
    reclamation = get_object_or_404(Reclamation, pk=pk)
    
    # Vérifier les permissions
    is_admin = request.user.is_staff or request.user.user_type in ['admin', 'teacher']
    if not is_admin and reclamation.utilisateur != request.user:
        messages.error(request, "Vous n'avez pas accès à cette réclamation.")
        return redirect('reclamations:list')

    # Commentaires (filtrer les commentaires internes si pas admin)
    commentaires = reclamation.commentaires.all()
    if not is_admin:
        commentaires = commentaires.filter(is_internal=False)
    
    # Réponses administrateur (seulement les publiées pour les utilisateurs)
    reponses_admin = reclamation.reponses_admin.all()
    if not is_admin:
        reponses_admin = reponses_admin.filter(statut='publiee')
        
        # Récupérer les réponses non lues AVANT de les marquer comme lues
        reponses_non_lues = list(reponses_admin.filter(lu_par_utilisateur=False))
        
        # Marquer les réponses comme lues par l'utilisateur SEULEMENT si c'est une consultation (GET)
        if request.method == 'GET' and reponses_non_lues:
            ReponseAdministrateur.objects.filter(
                id__in=[r.id for r in reponses_non_lues]
            ).update(
                lu_par_utilisateur=True,
                date_lecture=timezone.now()
            )

    # Formulaire de commentaire
    if request.method == 'POST' and 'add_comment' in request.POST:
        if is_admin:
            # Traitement manuel pour le template admin
            contenu = request.POST.get('contenu')
            fichier_joint = request.FILES.get('fichier_joint')
            is_internal = 'is_internal' in request.POST
            
            if contenu:
                commentaire = CommentaireReclamation.objects.create(
                    reclamation=reclamation,
                    auteur=request.user,
                    contenu=contenu,
                    fichier_joint=fichier_joint,
                    is_internal=is_internal
                )
                messages.success(request, "Votre commentaire a été ajouté.")
                return redirect('reclamations:detail', pk=pk)
        else:
            comment_form = CommentaireForm(request.POST, request.FILES)
            if comment_form.is_valid():
                commentaire = comment_form.save(commit=False)
                commentaire.reclamation = reclamation
                commentaire.auteur = request.user
                commentaire.save()
                
                messages.success(request, "Votre commentaire a été ajouté.")
                return redirect('reclamations:detail', pk=pk)
    else:
        if is_admin:
            comment_form = CommentaireAdminForm()
        else:
            comment_form = CommentaireForm()

    # Formulaire de réponse admin (seulement pour les admins)
    reponse_form = None
    if is_admin:
        if request.method == 'POST' and 'add_admin_response' in request.POST:
            reponse_form = ReponseAdministrateurQuickForm(request.POST, request.FILES)
            if reponse_form.is_valid():
                reponse = reponse_form.save(commit=False)
                reponse.reclamation = reclamation
                reponse.administrateur = request.user
                # Générer automatiquement un titre si pas fourni
                if not reponse.titre:
                    reponse.titre = f"Réponse à la réclamation #{reclamation.pk}"
                reponse.save()
                
                messages.success(request, "Votre réponse officielle a été publiée.")
                return redirect('reclamations:detail', pk=pk)
        else:
            reponse_form = ReponseAdministrateurQuickForm()

    context = {
        'reclamation': reclamation,
        'commentaires': commentaires,
        'reponses_admin': reponses_admin,
        'comment_form': comment_form,
        'reponse_form': reponse_form,
        'is_admin': is_admin,
        'historique': reclamation.historique.all()[:10],  # Derniers 10 changements
    }
    
    # Utiliser le template admin si l'utilisateur est admin
    if is_admin:
        return render(request, 'reclamations/admin_reclamation_detail.html', context)
    else:
        return render(request, 'reclamations/reclamation_detail.html', context)


@login_required
def reclamation_edit(request, pk):
    """Modifier une réclamation (admin seulement)"""
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        messages.error(request, "Vous n'avez pas la permission de modifier cette réclamation.")
        return redirect('reclamations:list')

    reclamation = get_object_or_404(Reclamation, pk=pk)
    ancien_statut = reclamation.statut

    if request.method == 'POST':
        form = ReclamationAdminForm(request.POST, instance=reclamation)
        if form.is_valid():
            reclamation = form.save()
            
            # Enregistrer le changement de statut si nécessaire
            if ancien_statut != reclamation.statut:
                SuiviReclamation.objects.create(
                    reclamation=reclamation,
                    ancien_statut=ancien_statut,
                    nouveau_statut=reclamation.statut,
                    modifie_par=request.user,
                    commentaire=f"Statut modifié par {request.user.username}"
                )
            
            messages.success(request, f"La réclamation '{reclamation.titre}' a été modifiée.")
            return redirect('reclamations:detail', pk=pk)
    else:
        form = ReclamationAdminForm(instance=reclamation)

    context = {
        'form': form,
        'reclamation': reclamation,
    }
    return render(request, 'reclamations/admin_reclamation_edit.html', context)


@login_required
def reclamation_assign(request, pk):
    """Assigner une réclamation à un utilisateur (AJAX)"""
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    if request.method == 'POST':
        reclamation = get_object_or_404(Reclamation, pk=pk)
        user_id = request.POST.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                ancien_assigne = reclamation.assigne_a
                reclamation.assigne_a = user
                reclamation.save()
                
                # Enregistrer le changement
                SuiviReclamation.objects.create(
                    reclamation=reclamation,
                    ancien_statut=reclamation.statut,
                    nouveau_statut=reclamation.statut,
                    modifie_par=request.user,
                    commentaire=f"Assigné à {user.username} par {request.user.username}"
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Réclamation assignée à {user.username}'
                })
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Utilisateur introuvable'})
        else:
            # Désassigner
            reclamation.assigne_a = None
            reclamation.save()
            return JsonResponse({'success': True, 'message': 'Réclamation désassignée'})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def reclamation_change_status(request, pk):
    """Changer le statut d'une réclamation (AJAX)"""
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    if request.method == 'POST':
        reclamation = get_object_or_404(Reclamation, pk=pk)
        nouveau_statut = request.POST.get('statut')
        commentaire = request.POST.get('commentaire', '')
        
        if nouveau_statut in dict(Reclamation.STATUS_CHOICES):
            ancien_statut = reclamation.statut
            reclamation.statut = nouveau_statut
            reclamation.save()
            
            # Enregistrer le changement
            SuiviReclamation.objects.create(
                reclamation=reclamation,
                ancien_statut=ancien_statut,
                nouveau_statut=nouveau_statut,
                modifie_par=request.user,
                commentaire=commentaire or f"Statut changé par {request.user.username}"
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Statut changé vers "{dict(Reclamation.STATUS_CHOICES)[nouveau_statut]}"'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Statut invalide'})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def dashboard_stats(request):
    """Statistiques pour le dashboard (AJAX)"""
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    stats = {
        'total': Reclamation.objects.count(),
        'ouvertes': Reclamation.objects.filter(statut='ouverte').count(),
        'en_cours': Reclamation.objects.filter(statut='en_cours').count(),
        'resolues': Reclamation.objects.filter(statut='resolue').count(),
        'urgentes': Reclamation.objects.filter(priorite='urgente', statut__in=['ouverte', 'en_cours']).count(),
        'mes_assignations': Reclamation.objects.filter(assigne_a=request.user, statut__in=['ouverte', 'en_cours']).count(),
    }
    
    # Réclamations par type
    types_stats = list(
        TypeReclamation.objects.filter(is_active=True).annotate(
            count=Count('reclamation')
        ).values('name', 'count', 'color')
    )
    
    return JsonResponse({
        'success': True,
        'stats': stats,
        'types_stats': types_stats
    })


@login_required
def reponses_lues_list(request):
    """Liste des réponses lues par l'utilisateur connecté"""
    
    # Récupérer toutes les réponses lues de l'utilisateur
    reponses_lues = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=request.user,
        statut='publiee',
        lu_par_utilisateur=True
    ).select_related('reclamation', 'administrateur').order_by('-date_lecture')
    
    # Filtres
    search = request.GET.get('search', '')
    if search:
        reponses_lues = reponses_lues.filter(
            Q(titre__icontains=search) |
            Q(contenu__icontains=search) |
            Q(reclamation__titre__icontains=search)
        )
    
    # Filtrer par réclamation si spécifié
    reclamation_id = request.GET.get('reclamation')
    if reclamation_id:
        reponses_lues = reponses_lues.filter(reclamation_id=reclamation_id)
    
    # Pagination
    paginator = Paginator(reponses_lues, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_lues': reponses_lues.count(),
        'total_reponses': ReponseAdministrateur.objects.filter(
            reclamation__utilisateur=request.user,
            statut='publiee'
        ).count(),
        'non_lues': ReponseAdministrateur.objects.filter(
            reclamation__utilisateur=request.user,
            statut='publiee',
            lu_par_utilisateur=False
        ).count(),
    }
    
    # Réclamations de l'utilisateur pour le filtre
    user_reclamations = Reclamation.objects.filter(
        utilisateur=request.user,
        reponses_admin__statut='publiee'
    ).distinct()
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'search': search,
        'reclamation_filter': reclamation_id,
        'user_reclamations': user_reclamations,
    }
    return render(request, 'reclamations/reponses_lues_list.html', context)


@login_required
def reclamations_assignees(request):
    """Liste des réclamations assignées à l'enseignant connecté"""
    
    # Vérifier que l'utilisateur est un enseignant
    if not (request.user.user_type == 'teacher' or request.user.is_staff):
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('accounts:dashboard')
    
    # Récupérer les réclamations assignées à cet enseignant
    reclamations_assignees = Reclamation.objects.filter(
        assigne_a=request.user
    ).select_related('utilisateur', 'type_reclamation').order_by('-created_at')
    
    # Filtres
    form = ReclamationSearchForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['search']:
            reclamations_assignees = reclamations_assignees.filter(
                Q(titre__icontains=form.cleaned_data['search']) |
                Q(description__icontains=form.cleaned_data['search']) |
                Q(utilisateur__first_name__icontains=form.cleaned_data['search']) |
                Q(utilisateur__last_name__icontains=form.cleaned_data['search'])
            )
        if form.cleaned_data['type_reclamation']:
            reclamations_assignees = reclamations_assignees.filter(type_reclamation=form.cleaned_data['type_reclamation'])
        if form.cleaned_data['statut']:
            reclamations_assignees = reclamations_assignees.filter(statut=form.cleaned_data['statut'])
        if form.cleaned_data['priorite']:
            reclamations_assignees = reclamations_assignees.filter(priorite=form.cleaned_data['priorite'])
        if form.cleaned_data['date_debut']:
            reclamations_assignees = reclamations_assignees.filter(created_at__gte=form.cleaned_data['date_debut'])
        if form.cleaned_data['date_fin']:
            reclamations_assignees = reclamations_assignees.filter(created_at__lte=form.cleaned_data['date_fin'])
    
    # Pagination
    paginator = Paginator(reclamations_assignees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_assignees': reclamations_assignees.count(),
        'ouvertes': reclamations_assignees.filter(statut='ouverte').count(),
        'en_cours': reclamations_assignees.filter(statut='en_cours').count(),
        'resolues': reclamations_assignees.filter(statut='resolue').count(),
        'urgentes': reclamations_assignees.filter(priorite='urgente').count(),
    }
    
    # Réclamations récentes (dernières 7 jours)
    from datetime import timedelta
    date_limite = timezone.now() - timedelta(days=7)
    nouvelles_assignations = reclamations_assignees.filter(created_at__gte=date_limite).count()
    stats['nouvelles'] = nouvelles_assignations
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'stats': stats,
        'teacher_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'reclamations/reclamations_assignees.html', context)


def get_teacher_reclamations_stats(user):
    """Obtenir les statistiques des réclamations pour un enseignant"""
    if not (user.user_type == 'teacher' or user.is_staff):
        return None
    
    # Réclamations assignées à cet enseignant
    reclamations_assignees = Reclamation.objects.filter(assigne_a=user)
    
    # Statistiques
    stats = {
        'total_assignees': reclamations_assignees.count(),
        'ouvertes': reclamations_assignees.filter(statut='ouverte').count(),
        'en_cours': reclamations_assignees.filter(statut='en_cours').count(),
        'resolues': reclamations_assignees.filter(statut='resolue').count(),
        'urgentes': reclamations_assignees.filter(priorite='urgente').count(),
    }
    
    # Réclamations récentes (dernières 7 jours)
    from datetime import timedelta
    date_limite = timezone.now() - timedelta(days=7)
    stats['nouvelles'] = reclamations_assignees.filter(created_at__gte=date_limite).count()
    
    # Réclamations les plus récentes (3 dernières)
    stats['recentes'] = reclamations_assignees.select_related('utilisateur', 'type_reclamation').order_by('-created_at')[:3]
    
    return stats


@login_required
def admin_response_create(request, pk):
    """Créer une réponse administrateur détaillée"""
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        messages.error(request, "Vous n'avez pas la permission de créer une réponse.")
        return redirect('reclamations:list')

    reclamation = get_object_or_404(Reclamation, pk=pk)

    if request.method == 'POST':
        form = ReponseAdministrateurForm(request.POST, request.FILES)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.reclamation = reclamation
            reponse.administrateur = request.user
            reponse.save()
            
            messages.success(request, f"Réponse créée avec succès pour la réclamation '{reclamation.titre}'.")
            return redirect('reclamations:detail', pk=pk)
    else:
        # Pré-remplir le titre
        initial_data = {
            'titre': f"Réponse officielle - {reclamation.titre}",
        }
        form = ReponseAdministrateurForm(initial=initial_data)

    context = {
        'form': form,
        'reclamation': reclamation,
    }
    return render(request, 'reclamations/admin_response_create.html', context)


@login_required
def admin_response_edit(request, pk, response_pk):
    """Modifier une réponse administrateur"""
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        messages.error(request, "Vous n'avez pas la permission de modifier cette réponse.")
        return redirect('reclamations:list')

    reclamation = get_object_or_404(Reclamation, pk=pk)
    reponse = get_object_or_404(ReponseAdministrateur, pk=response_pk, reclamation=reclamation)

    # Vérifier que l'utilisateur peut modifier cette réponse
    if reponse.administrateur != request.user and not request.user.is_superuser:
        messages.error(request, "Vous ne pouvez modifier que vos propres réponses.")
        return redirect('reclamations:detail', pk=pk)

    if request.method == 'POST':
        form = ReponseAdministrateurForm(request.POST, request.FILES, instance=reponse)
        if form.is_valid():
            form.save()
            messages.success(request, "Réponse modifiée avec succès.")
            return redirect('reclamations:detail', pk=pk)
    else:
        form = ReponseAdministrateurForm(instance=reponse)

    context = {
        'form': form,
        'reclamation': reclamation,
        'reponse': reponse,
    }
    return render(request, 'reclamations/admin_response_edit.html', context)


@login_required
def admin_response_delete(request, pk, response_pk):
    """Supprimer une réponse administrateur"""
    if not (request.user.is_staff or request.user.user_type in ['admin', 'teacher']):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    if request.method == 'POST':
        reclamation = get_object_or_404(Reclamation, pk=pk)
        reponse = get_object_or_404(ReponseAdministrateur, pk=response_pk, reclamation=reclamation)
        
        # Vérifier que l'utilisateur peut supprimer cette réponse
        if reponse.administrateur != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Vous ne pouvez supprimer que vos propres réponses'})
        
        reponse.delete()
        return JsonResponse({'success': True, 'message': 'Réponse supprimée avec succès'})

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
