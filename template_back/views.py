from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg
from django.contrib import messages
from gamification.models import Quiz, QuizAttempt, UserProfile, Badge
from cours.models import Course, CourseModule, CourseResource
from forum.models import Category, Topic, Post
from forum.forms import CategoryForm

User = get_user_model()

@login_required
def dashboard(request):
    # Statistiques pour le dashboard admin
    context = {
        'total_users': User.objects.count(),
        'students_count': User.objects.filter(user_type='student').count(),
        'teachers_count': User.objects.filter(user_type='teacher').count(),
        'admins_count': User.objects.filter(user_type='admin').count(),
        'verified_users': User.objects.filter(is_verified=True).count(),
        'recent_users': User.objects.order_by('-created_at')[:5],
        'current_user': request.user,

        # Statistiques de gamification
        'total_quizzes': Quiz.objects.count(),
        'total_attempts': QuizAttempt.objects.count(),
        'total_badges': Badge.objects.count(),
        'active_gamification_users': UserProfile.objects.filter(user__is_active=True).count(),
        'top_gamification_users': UserProfile.objects.order_by('-total_points')[:5],
        'recent_quiz_attempts': QuizAttempt.objects.select_related('student', 'quiz').order_by('-started_at')[:5],

        # Statistiques des cours
        'total_courses': Course.objects.count(),
        'total_modules': CourseModule.objects.count(),
        'total_resources': CourseResource.objects.count(),
        'recent_courses': Course.objects.order_by('-created_at')[:5],
        'courses_by_subject': Course.objects.values('subject__name').annotate(count=Count('id')).order_by('-count')[:5],
    }
    return render(request, 'dashboard.html', context)


# ============================================
# GESTION DES CATÉGORIES DU FORUM
# ============================================

@login_required
def forum_categories_list(request):
    """Liste des catégories du forum pour l'admin"""
    if request.user.user_type != 'admin' and not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('template_back:dashboard')
    
    categories = Category.objects.all().annotate(
        topics_count=Count('topics', distinct=True),
        posts_count=Count('topics__posts', distinct=True)
    ).order_by('order', 'name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'template_back/forum_categories_list.html', context)


@login_required
def forum_category_create(request):
    """Créer une nouvelle catégorie"""
    if request.user.user_type != 'admin' and not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('template_back:dashboard')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Catégorie créée avec succès!')
            return redirect('template_back:forum_categories_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'action': 'Créer',
    }
    return render(request, 'template_back/forum_category_form.html', context)


@login_required
def forum_category_edit(request, pk):
    """Modifier une catégorie existante"""
    if request.user.user_type != 'admin' and not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('template_back:dashboard')
    
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Catégorie modifiée avec succès!')
            return redirect('template_back:forum_categories_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'action': 'Modifier',
    }
    return render(request, 'template_back/forum_category_form.html', context)


@login_required
def forum_category_delete(request, pk):
    """Supprimer une catégorie"""
    if request.user.user_type != 'admin' and not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('template_back:dashboard')
    
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'✅ Catégorie "{category_name}" supprimée avec succès!')
        return redirect('template_back:forum_categories_list')
    
    context = {
        'category': category,
    }
    return render(request, 'template_back/forum_category_confirm_delete.html', context)


@login_required
def forum_category_toggle_active(request, pk):
    """Activer/Désactiver une catégorie"""
    if request.user.user_type != 'admin' and not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('template_back:dashboard')
    
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save()
    
    status = "activée" if category.is_active else "désactivée"
    messages.success(request, f'✅ Catégorie "{category.name}" {status}!')
    return redirect('template_back:forum_categories_list')
