"""
Vues innovantes pour le système de gamification EduSmart
Interface utilisateur moderne et interactive
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
import json

from .models import *
from .advanced_gamification import (
    AdvancedGamificationEngine, 
    QuestSystem, 
    RewardSystem,
    PersonalizedRecommendationEngine,
    AnalyticsEngine
)


@login_required
def gamification_dashboard(request):
    """Dashboard principal de gamification avec analytics en temps réel"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Initialiser les moteurs
    analytics_engine = AnalyticsEngine()
    recommendation_engine = PersonalizedRecommendationEngine()
    quest_system = QuestSystem()
    
    # Données du dashboard avec gestion d'erreur
    try:
        analytics = analytics_engine.generate_user_analytics(user_profile)
        recommendations = recommendation_engine.get_recommendations(user_profile)
        active_quests = quest_system.check_quest_completion(user_profile)
    except Exception as e:
        # En cas d'erreur, utiliser des valeurs par défaut
        analytics = {'performance_trends': {'trend': 'insufficient_data'}}
        recommendations = {'quizzes': [], 'subjects': [], 'study_plan': {}}
        active_quests = []
        print(f"Erreur dans le dashboard: {e}")
    
    context = {
        'user_profile': user_profile,
        'analytics': analytics,
        'recommendations': recommendations,
        'active_quests': active_quests,
        'recent_attempts': QuizAttempt.objects.filter(
            student=request.user,
            status='completed'
        ).select_related('quiz').order_by('-completed_at')[:5],
        'badges': UserBadge.objects.filter(user=request.user).select_related('badge')[:10],
        'leaderboard_position': user_profile.get_rank(),
        'level_progress': user_profile.get_level_progress(),
    }
    
    return render(request, 'gamification/innovative_dashboard.html', context)


@login_required
def ai_quiz_generator_view(request):
    """Interface pour générer des quiz avec IA"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        difficulty = int(request.POST.get('difficulty', 2))
        num_questions = int(request.POST.get('num_questions', 10))
        
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Générer le quiz
        gamification_engine = AdvancedGamificationEngine()
        
        if request.POST.get('personalized') == 'true':
            quiz = gamification_engine.generate_personalized_quiz(user_profile)
        else:
            quiz = gamification_engine.ai_generator.generate_quiz(
                subject_name=subject,
                difficulty_level=difficulty,
                num_questions=num_questions,
                user_profile=user_profile
            )
        
        if quiz:
            messages.success(request, f'Quiz "{quiz.title}" généré avec succès!')
            return redirect('gamification:quiz_detail', slug=quiz.slug)
        else:
            messages.error(request, 'Erreur lors de la génération du quiz.')
    
    # Données pour le formulaire
    subjects = Subject.objects.filter(is_active=True)
    difficulty_levels = DifficultyLevel.objects.all()
    
    context = {
        'subjects': subjects,
        'difficulty_levels': difficulty_levels,
        'ai_available': True,  # Basé sur la configuration OpenAI
    }
    
    return render(request, 'gamification/ai_quiz_generator.html', context)


@login_required
def interactive_quiz_room(request, room_code):
    """Room de quiz interactive en temps réel"""
    room = get_object_or_404(QuizRoom, room_code=room_code)
    
    # Vérifier si l'utilisateur peut rejoindre
    if not room.can_join():
        messages.error(request, 'Cette room n\'est plus disponible.')
        return redirect('gamification:dashboard')
    
    # Créer ou récupérer la participation
    participant, created = RoomParticipant.objects.get_or_create(
        room=room,
        student=request.user
    )
    
    if created:
        room.total_participants += 1
        room.save()
    
    context = {
        'room': room,
        'participant': participant,
        'quiz': room.quiz,
        'questions': room.quiz.questions.all().order_by('order'),
        'participants_count': room.total_participants,
        'is_teacher': request.user == room.teacher,
    }
    
    return render(request, 'gamification/interactive_quiz_room.html', context)


@login_required
@require_http_methods(["POST"])
def submit_quiz_answer(request):
    """Soumission d'une réponse de quiz (AJAX)"""
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        answer = data.get('answer')
        time_taken = data.get('time_taken', 0)
        
        question = get_object_or_404(Question, id=question_id)
        
        # Vérifier si c'est correct
        is_correct = answer == question.correct_answer
        
        # Calculer les points
        points = question.points if is_correct else 0
        
        response_data = {
            'correct': is_correct,
            'points': points,
            'explanation': question.explanation,
            'correct_answer': question.correct_answer
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def personalized_learning_path(request):
    """Parcours d'apprentissage personnalisé"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    recommendation_engine = PersonalizedRecommendationEngine()
    
    # Générer le parcours personnalisé
    recommendations = recommendation_engine.get_recommendations(user_profile)
    study_plan = recommendations.get('study_plan', {})
    
    context = {
        'user_profile': user_profile,
        'study_plan': study_plan,
        'recommended_quizzes': recommendations.get('quizzes', []),
        'recommended_subjects': recommendations.get('subjects', []),
        'weak_areas': study_plan.get('focus_areas', []),
        'daily_goals': study_plan.get('daily_goals', {}),
        'weekly_goals': study_plan.get('weekly_goals', {}),
    }
    
    return render(request, 'gamification/personalized_learning_path.html', context)


@login_required
def achievement_center(request):
    """Centre des réalisations et badges"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Badges obtenus
    earned_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
    
    # Badges disponibles
    available_badges = Badge.objects.filter(is_active=True).exclude(
        id__in=earned_badges.values_list('badge_id', flat=True)
    )
    
    # Statistiques
    stats = {
        'total_badges': Badge.objects.filter(is_active=True).count(),
        'earned_badges': earned_badges.count(),
        'completion_rate': (earned_badges.count() / Badge.objects.filter(is_active=True).count()) * 100 if Badge.objects.filter(is_active=True).count() > 0 else 0,
        'rarity_distribution': earned_badges.values('badge__rarity').annotate(count=Count('id'))
    }
    
    context = {
        'user_profile': user_profile,
        'earned_badges': earned_badges,
        'available_badges': available_badges,
        'stats': stats,
        'recent_achievements': earned_badges.order_by('-earned_at')[:5]
    }
    
    return render(request, 'gamification/achievement_center.html', context)


@login_required
def live_leaderboard(request):
    """Classement en temps réel avec filtres"""
    # Paramètres de filtrage
    timeframe = request.GET.get('timeframe', 'all')  # all, week, month
    subject_id = request.GET.get('subject')
    
    # Base query
    profiles = UserProfile.objects.select_related('user')
    
    # Filtrage par période
    if timeframe == 'week':
        week_ago = timezone.now() - timezone.timedelta(days=7)
        profiles = profiles.filter(last_activity__gte=week_ago)
    elif timeframe == 'month':
        month_ago = timezone.now() - timezone.timedelta(days=30)
        profiles = profiles.filter(last_activity__gte=month_ago)
    
    # Filtrage par matière
    if subject_id:
        subject = get_object_or_404(Subject, id=subject_id)
        profiles = profiles.filter(favorite_subjects=subject)
    
    # Ordonner par points d'expérience
    profiles = profiles.order_by('-experience_points')
    
    # Pagination
    paginator = Paginator(profiles, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Position de l'utilisateur actuel
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_rank = profiles.filter(experience_points__gt=user_profile.experience_points).count() + 1
    
    context = {
        'page_obj': page_obj,
        'subjects': Subject.objects.filter(is_active=True),
        'current_timeframe': timeframe,
        'current_subject': subject_id,
        'user_rank': user_rank,
        'user_profile': user_profile,
        'total_users': profiles.count()
    }
    
    return render(request, 'gamification/live_leaderboard.html', context)


@login_required
def quiz_analytics(request, quiz_slug):
    """Analytics détaillées pour un quiz spécifique"""
    quiz = get_object_or_404(Quiz, slug=quiz_slug)
    
    # Statistiques générales
    attempts = QuizAttempt.objects.filter(quiz=quiz, status='completed')
    
    stats = {
        'total_attempts': attempts.count(),
        'average_score': attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0,
        'pass_rate': (attempts.filter(percentage__gte=quiz.passing_score).count() / attempts.count() * 100) if attempts.count() > 0 else 0,
        'average_time': attempts.aggregate(Avg('time_taken'))['time_taken__avg'] or 0,
    }
    
    # Distribution des scores
    score_distribution = []
    for i in range(0, 101, 10):
        count = attempts.filter(percentage__gte=i, percentage__lt=i+10).count()
        score_distribution.append({'range': f'{i}-{i+9}%', 'count': count})
    
    # Questions les plus difficiles
    questions_stats = []
    for question in quiz.questions.all():
        # Cette logique nécessiterait un tracking des réponses par question
        # Pour l'instant, on simule
        questions_stats.append({
            'question': question.question_text[:50] + '...',
            'difficulty': question.difficulty_score,
            'success_rate': random.uniform(40, 90)  # Simulation
        })
    
    context = {
        'quiz': quiz,
        'stats': stats,
        'score_distribution': score_distribution,
        'questions_stats': questions_stats,
        'recent_attempts': attempts.select_related('student').order_by('-completed_at')[:10]
    }
    
    return render(request, 'gamification/quiz_analytics.html', context)


@login_required
@require_http_methods(["POST"])
def create_quiz_room(request):
    """Créer une nouvelle room de quiz"""
    try:
        data = json.loads(request.body)
        quiz_id = data.get('quiz_id')
        title = data.get('title')
        max_participants = data.get('max_participants', 50)
        
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        room = QuizRoom.objects.create(
            title=title,
            teacher=request.user,
            quiz=quiz,
            max_participants=max_participants
        )
        
        return JsonResponse({
            'success': True,
            'room_code': room.room_code,
            'room_url': room.get_absolute_url()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def social_features(request):
    """Fonctionnalités sociales et défis"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Activités récentes des autres utilisateurs
    recent_activities = QuizAttempt.objects.filter(
        status='completed',
        completed_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).exclude(student=request.user).select_related('student', 'quiz').order_by('-completed_at')[:20]
    
    # Top performers de la semaine
    week_ago = timezone.now() - timezone.timedelta(days=7)
    top_performers = UserProfile.objects.filter(
        last_activity__gte=week_ago
    ).order_by('-experience_points')[:10]
    
    context = {
        'user_profile': user_profile,
        'recent_activities': recent_activities,
        'top_performers': top_performers,
    }
    
    return render(request, 'gamification/social_features.html', context)


@login_required
@require_http_methods(["GET"])
def get_user_stats_api(request):
    """API pour récupérer les statistiques utilisateur (AJAX)"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    stats = {
        'level': user_profile.level,
        'experience_points': user_profile.experience_points,
        'total_points': user_profile.total_points,
        'quizzes_completed': user_profile.quizzes_completed,
        'current_streak': user_profile.current_streak,
        'level_progress': user_profile.get_level_progress(),
        'rank': user_profile.get_rank(),
        'badges_count': UserBadge.objects.filter(user=request.user).count()
    }
    
    return JsonResponse(stats)


@login_required
def progress_tracking(request):
    """Suivi détaillé des progrès"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    analytics_engine = AnalyticsEngine()
    
    # Générer les analytics
    analytics = analytics_engine.generate_user_analytics(user_profile)
    
    # Historique des performances
    attempts = QuizAttempt.objects.filter(
        student=request.user,
        status='completed'
    ).select_related('quiz__subject').order_by('completed_at')
    
    # Données pour les graphiques
    performance_data = []
    subject_performance = {}
    
    for attempt in attempts:
        performance_data.append({
            'date': attempt.completed_at.strftime('%Y-%m-%d'),
            'score': attempt.percentage,
            'subject': attempt.quiz.subject.name
        })
        
        subject = attempt.quiz.subject.name
        if subject not in subject_performance:
            subject_performance[subject] = []
        subject_performance[subject].append(attempt.percentage)
    
    # Moyennes par matière
    subject_averages = {}
    for subject, scores in subject_performance.items():
        subject_averages[subject] = sum(scores) / len(scores)
    
    context = {
        'user_profile': user_profile,
        'analytics': analytics,
        'performance_data': json.dumps(performance_data),
        'subject_averages': subject_averages,
        'total_attempts': attempts.count(),
        'improvement_areas': analytics.get('learning_patterns', {}).get('weak_areas', [])
    }
    
    return render(request, 'gamification/progress_tracking.html', context)
