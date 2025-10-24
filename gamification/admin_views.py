from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg, Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Quiz, QuizAttempt, UserProfile, UserBadge, UserAchievement,
    Subject, DifficultyLevel, Badge, Achievement, Leaderboard
)
from accounts.models import CustomUser

def is_admin(user):
    return user.is_staff or user.user_type == 'admin'

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Tableau de bord admin avec statistiques de gamification"""
    
    # Statistiques générales
    total_users = CustomUser.objects.count()
    total_quizzes = Quiz.objects.count()
    total_attempts = QuizAttempt.objects.count()
    total_badges = Badge.objects.count()
    
    # Statistiques des dernières 30 jours
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_attempts = QuizAttempt.objects.filter(started_at__gte=thirty_days_ago)
    recent_users = CustomUser.objects.filter(date_joined__gte=thirty_days_ago)
    
    # Top utilisateurs par points
    top_users = UserProfile.objects.order_by('-total_points')[:10]
    
    # Top matières par popularité
    popular_subjects = Subject.objects.annotate(
        quiz_count=Count('quizzes'),
        attempt_count=Count('quizzes__attempts')
    ).order_by('-attempt_count')[:5]
    
    # Statistiques des badges
    badge_stats = Badge.objects.annotate(
        earned_count=Count('users')
    ).order_by('-earned_count')[:5]
    
    # Statistiques des quiz
    quiz_stats = Quiz.objects.annotate(
        attempt_count=Count('attempts'),
        avg_score=Avg('attempts__percentage')
    ).order_by('-attempt_count')[:5]
    
    # Activité récente
    recent_activity = QuizAttempt.objects.select_related(
        'student', 'quiz'
    ).order_by('-started_at')[:10]
    
    # Statistiques par niveau de difficulté
    difficulty_stats = DifficultyLevel.objects.annotate(
        quiz_count=Count('quizzes'),
        attempt_count=Count('quizzes__attempts'),
        avg_score=Avg('quizzes__attempts__percentage')
    ).order_by('level')
    
    context = {
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'total_badges': total_badges,
        'recent_attempts_count': recent_attempts.count(),
        'recent_users_count': recent_users.count(),
        'top_users': top_users,
        'popular_subjects': popular_subjects,
        'badge_stats': badge_stats,
        'quiz_stats': quiz_stats,
        'recent_activity': recent_activity,
        'difficulty_stats': difficulty_stats,
    }
    
    return render(request, 'gamification/admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_quiz_management(request):
    """Gestion des quiz par l'admin"""
    
    quizzes = Quiz.objects.select_related('subject', 'difficulty').annotate(
        attempt_count=Count('attempts'),
        avg_score=Avg('attempts__percentage')
    ).order_by('-created_at')
    
    subjects = Subject.objects.all()
    difficulties = DifficultyLevel.objects.all()
    
    context = {
        'quizzes': quizzes,
        'subjects': subjects,
        'difficulties': difficulties,
    }
    
    return render(request, 'gamification/admin/quiz_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_management(request):
    """Gestion des utilisateurs et leurs statistiques de gamification"""
    
    users = CustomUser.objects.select_related('gamification_profile').order_by('-date_joined')
    
    # Statistiques par type d'utilisateur
    user_stats = CustomUser.objects.values('user_type').annotate(
        count=Count('id'),
        total_points=Sum('gamification_profile__total_points'),
        avg_level=Avg('gamification_profile__level')
    )
    
    context = {
        'users': users,
        'user_stats': user_stats,
    }
    
    return render(request, 'gamification/admin/user_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_leaderboard_management(request):
    """Gestion des classements"""
    
    # Classement global
    global_leaderboard = UserProfile.objects.select_related('user').order_by('-total_points')[:50]
    
    # Classements par matière
    subject_leaderboards = {}
    for subject in Subject.objects.all():
        subject_leaderboards[subject] = UserProfile.objects.filter(
            user__quiz_attempts__quiz__subject=subject
        ).annotate(
            subject_points=Sum('user__quiz_attempts__points_earned')
        ).order_by('-subject_points')[:10]
    
    context = {
        'global_leaderboard': global_leaderboard,
        'subject_leaderboards': subject_leaderboards,
    }
    
    return render(request, 'gamification/admin/leaderboard_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_badge_management(request):
    """Gestion des badges"""
    
    badges = Badge.objects.annotate(
        earned_count=Count('users'),
        recent_earned=Count('users', filter=Q(users__earned_at__gte=timezone.now() - timedelta(days=7)))
    ).order_by('-created_at')
    
    # Statistiques des badges les plus populaires
    popular_badges = Badge.objects.annotate(
        earned_count=Count('users')
    ).order_by('-earned_count')[:10]
    
    context = {
        'badges': badges,
        'popular_badges': popular_badges,
    }
    
    return render(request, 'gamification/admin/badge_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_analytics(request):
    """Analyses et rapports détaillés"""
    
    # Données pour les graphiques
    last_30_days = []
    for i in range(30):
        date = timezone.now() - timedelta(days=i)
        attempts = QuizAttempt.objects.filter(
            started_at__date=date.date()
        ).count()
        last_30_days.append({
            'date': date.strftime('%Y-%m-%d'),
            'attempts': attempts
        })
    
    # Répartition des scores
    score_ranges = [
        {'range': '0-20%', 'count': QuizAttempt.objects.filter(percentage__lt=20).count()},
        {'range': '20-40%', 'count': QuizAttempt.objects.filter(percentage__gte=20, percentage__lt=40).count()},
        {'range': '40-60%', 'count': QuizAttempt.objects.filter(percentage__gte=40, percentage__lt=60).count()},
        {'range': '60-80%', 'count': QuizAttempt.objects.filter(percentage__gte=60, percentage__lt=80).count()},
        {'range': '80-100%', 'count': QuizAttempt.objects.filter(percentage__gte=80).count()},
    ]
    
    context = {
        'last_30_days': last_30_days,
        'score_ranges': score_ranges,
    }
    
    return render(request, 'gamification/admin/analytics.html', context)
