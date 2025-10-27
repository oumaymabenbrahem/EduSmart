from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    UserProfileForm, 
    PasswordChangeForm
)

User = get_user_model()


def register_view(request):
    """Vue d'inscription des utilisateurs"""
    # Vérifier si c'est un admin qui ajoute un utilisateur
    from_admin = request.user.is_authenticated and request.user.user_type == 'admin'
    
    if request.user.is_authenticated and not from_admin:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f'Compte créé avec succès pour {username}!')
                
                # Si admin ajoute un utilisateur, rediriger vers la liste
                if from_admin:
                    return redirect('accounts:users_list')
                
                # Connexion automatique après inscription (utilisateurs publics)
                user = authenticate(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1']
                )
                if user:
                    login(request, user)
                    # Redirection selon le type d'utilisateur
                    if user.user_type == 'admin':
                        return redirect('template_back:dashboard')
                    else:
                        # Rediriger vers la page d'accueil (index) pour étudiants et enseignants
                        return redirect('template_front:index')
            except IntegrityError:
                # Gestion d'erreur si le nom d'utilisateur existe déjà (sécurité supplémentaire)
                messages.error(request, 'Ce nom d\'utilisateur est déjà pris. Veuillez en choisir un autre.')
                form.add_error('username', 'Ce nom d\'utilisateur est déjà pris.')
    else:
        form = CustomUserCreationForm()
    
    # Utiliser le template admin si l'utilisateur est admin
    if from_admin:
        return render(request, 'accounts/admin_register.html', {'form': form})
    elif 'from_admin' in request.GET:
        return render(request, 'accounts/register.html', {'form': form})
    else:
        return render(request, 'accounts/front_register.html', {'form': form})


def login_view(request):
    """Vue de connexion des utilisateurs"""
    if request.user.is_authenticated:
        # Rediriger vers l'index si déjà connecté (sauf admin)
        if request.user.user_type == 'admin':
            return redirect('template_back:dashboard')
        else:
            return redirect('template_front:index')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Afficher le prénom s'il existe, sinon le nom d'utilisateur
                display_name = user.first_name if user.first_name else user.username
                messages.success(request, f'Bienvenue {display_name} !')
                
                # Redirection conditionnelle selon le type d'utilisateur
                next_url = request.GET.get('next')
                if not next_url:
                    if user.user_type == 'admin':
                        next_url = 'template_back:dashboard'
                    else:
                        # Rediriger vers la page d'accueil pour étudiants et enseignants
                        next_url = 'template_front:index'
                return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = CustomAuthenticationForm()
    
    # Utiliser le template front si on vient du site public
    if 'from_admin' in request.GET:
        return render(request, 'accounts/login.html', {'form': form})
    else:
        return render(request, 'accounts/front_login.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('template_front:index')


@login_required
def dashboard_view(request):
    """Tableau de bord utilisateur"""
    user = request.user
    context = {
        'user': user,
        'total_users': User.objects.count(),
        'students_count': User.objects.filter(user_type='student').count(),
        'teachers_count': User.objects.filter(user_type='teacher').count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request, pk=None):
    """Vue pour afficher le profil d'un utilisateur"""
    if pk:
        profile_user = get_object_or_404(User, pk=pk)
    else:
        profile_user = request.user
    
    context = {
        'profile_user': profile_user,
        'is_own_profile': profile_user == request.user,
    }
    
    # Utiliser le template admin si l'utilisateur connecté est admin
    if request.user.user_type == 'admin':
        # Si c'est son propre profil sans pk spécifié
        if not pk:
            return render(request, 'accounts/admin_profile.html', context)
        # Si c'est le profil d'un autre utilisateur
        else:
            return render(request, 'accounts/admin_profile_detail.html', context)
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """Vue d'édition du profil"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Utiliser le template admin si l'utilisateur est admin
    if request.user.user_type == 'admin':
        return render(request, 'accounts/admin_edit_profile.html', {'form': form})
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def change_password_view(request):
    """Vue de changement de mot de passe"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mot de passe changé avec succès!')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    # Utiliser le template admin si l'utilisateur est admin
    if request.user.user_type == 'admin':
        return render(request, 'accounts/admin_change_password.html', {'form': form})
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def users_list_view(request):
    """Liste des utilisateurs avec recherche et filtrage"""
    users = User.objects.all()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filtrage par type d'utilisateur
    user_type_filter = request.GET.get('user_type', '')
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    # Pagination
    paginator = Paginator(users, 12)  # 12 utilisateurs par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques pour le template admin
    context = {
        'users': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'user_types': User.USER_TYPE_CHOICES,
        'total_users': User.objects.count(),
        'students_count': User.objects.filter(user_type='student').count(),
        'teachers_count': User.objects.filter(user_type='teacher').count(),
        'admins_count': User.objects.filter(user_type='admin').count(),
    }
    
    # Utiliser le template admin si l'utilisateur est admin
    if request.user.user_type == 'admin':
        return render(request, 'accounts/admin_users_list.html', context)
    
    return render(request, 'accounts/users_list.html', context)


@login_required
def delete_account_view(request):
    """Vue de suppression de compte"""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Votre compte a été supprimé avec succès.')
        return redirect('template_front:index')
    
    return render(request, 'accounts/delete_account.html')


def ajax_check_username(request):
    """Vérification AJAX de la disponibilité du nom d'utilisateur"""
    username = request.GET.get('username', '')
    is_available = not User.objects.filter(username=username).exists()
    return JsonResponse({'is_available': is_available})


def ajax_check_email(request):
    """Vérification AJAX de la disponibilité de l'email"""
    email = request.GET.get('email', '')
    is_available = not User.objects.filter(email=email).exists()
    return JsonResponse({'is_available': is_available})
