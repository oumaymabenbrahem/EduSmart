from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
import json

from .models import (
    Subject, DifficultyLevel, Quiz, Question, QuizAttempt, 
    Badge, UserBadge, UserProfile, Leaderboard, Achievement, UserAchievement
)
from .ai_quiz_generator import AIQuizGenerator, BadgeAwarder, LeaderboardManager


def gamification_home(request):
    """Page d'accueil de la gamification"""
    subjects = Subject.objects.filter(is_active=True)
    difficulty_levels = DifficultyLevel.objects.all()
    
    # Statistiques générales
    total_quizzes = Quiz.objects.filter(status='published').count()
    total_users = UserProfile.objects.count()
    
    # Classement global (top 5)
    top_users = UserProfile.objects.order_by('-experience_points')[:5]
    
    context = {
        'subjects': subjects,
        'difficulty_levels': difficulty_levels,
        'total_quizzes': total_quizzes,
        'total_users': total_users,
        'top_users': top_users,
    }
    
    return render(request, 'gamification/home.html', context)


@login_required
def select_quiz(request):
    """Page de sélection de quiz"""
    subjects = Subject.objects.filter(is_active=True)
    difficulty_levels = DifficultyLevel.objects.all()
    
    # Récupérer les quiz récents
    recent_quizzes = Quiz.objects.filter(status='published').order_by('-created_at')[:6]
    
    # Récupérer les tentatives de l'utilisateur
    user_attempts = QuizAttempt.objects.filter(student=request.user).order_by('-started_at')[:5]
    
    context = {
        'subjects': subjects,
        'difficulty_levels': difficulty_levels,
        'recent_quizzes': recent_quizzes,
        'user_attempts': user_attempts,
    }
    
    return render(request, 'gamification/select_quiz.html', context)


@login_required
def generate_quiz(request):
    """Génère un quiz avec IA"""
    if request.method == 'POST':
        subject_name = request.POST.get('subject')
        difficulty_level = int(request.POST.get('difficulty', 1))
        num_questions = int(request.POST.get('num_questions', 10))
        
        # Récupérer ou créer le profil de gamification
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Générer le quiz avec IA
        generator = AIQuizGenerator()
        quiz = generator.generate_quiz(subject_name, difficulty_level, num_questions, user_profile)
        
        if quiz:
            messages.success(request, f'Quiz "{quiz.title}" généré avec succès !')
            return redirect('gamification:quiz_detail', slug=quiz.slug)
        else:
            messages.error(request, 'Erreur lors de la génération du quiz.')
    
    return redirect('gamification:select_quiz')


@login_required
def quiz_detail(request, slug):
    """Détails d'un quiz"""
    quiz = get_object_or_404(Quiz, slug=slug, status='published')
    questions = quiz.questions.filter(is_active=True).order_by('order')
    
    # Vérifier les tentatives précédentes
    user_attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz)
    can_attempt = user_attempts.count() < quiz.max_attempts
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'user_attempts': user_attempts,
        'can_attempt': can_attempt,
        'next_attempt': user_attempts.count() + 1,
    }
    
    return render(request, 'gamification/quiz_detail.html', context)


@login_required
def start_quiz(request, slug):
    """Commence un quiz"""
    quiz = get_object_or_404(Quiz, slug=slug, status='published')
    
    # Vérifier les tentatives
    user_attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz)
    if user_attempts.count() >= quiz.max_attempts:
        messages.error(request, 'Vous avez atteint le nombre maximum de tentatives pour ce quiz.')
        return redirect('gamification:quiz_detail', slug=quiz.slug)
    
    # Créer une nouvelle tentative
    attempt_number = user_attempts.count() + 1
    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        attempt_number=attempt_number,
        status='in_progress'
    )
    
    return redirect('gamification:take_quiz', attempt_id=attempt.id)


@login_required
def take_quiz(request, attempt_id):
    """Prendre un quiz"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.status != 'in_progress':
        messages.error(request, 'Cette tentative n\'est plus active.')
        return redirect('gamification:quiz_detail', slug=attempt.quiz.slug)
    
    questions = attempt.quiz.questions.filter(is_active=True).order_by('order')
    
    context = {
        'attempt': attempt,
        'questions': questions,
        'time_limit': attempt.quiz.time_limit * 60,  # Convertir en secondes
    }
    
    return render(request, 'gamification/take_quiz.html', context)


@login_required
@require_http_methods(["POST"])
def submit_quiz(request, attempt_id):
    """Soumet les réponses du quiz"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'Tentative non active'}, status=400)
    
    # Récupérer les réponses
    answers = {}
    questions = attempt.quiz.questions.filter(is_active=True).order_by('order')
    
    for question in questions:
        answer_key = f'question_{question.id}'
        if answer_key in request.POST:
            answers[str(question.id)] = request.POST[answer_key]
    
    # Calculer le score
    correct_answers = 0
    total_questions = questions.count()
    points_earned = 0
    
    for question in questions:
        question_id = str(question.id)
        if question_id in answers:
            user_answer = answers[question_id]
            if user_answer == question.correct_answer:
                correct_answers += 1
                points_earned += question.points
    
    # Calculer les pourcentages
    percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    score = correct_answers
    
    # Calculer le temps pris
    time_taken = int(request.POST.get('time_taken', 0))
    
    # Mettre à jour la tentative
    attempt.score = score
    attempt.percentage = percentage
    attempt.points_earned = points_earned
    attempt.experience_earned = int(points_earned * 0.5)  # 50% des points en expérience
    attempt.time_taken = time_taken
    attempt.answers = answers
    attempt.status = 'completed'
    attempt.completed_at = timezone.now()
    attempt.save()
    
    # Mettre à jour le profil de gamification
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_profile.quizzes_completed += 1
    user_profile.total_attempts += 1
    user_profile.total_points += points_earned
    user_profile.experience_points += attempt.experience_earned
    
    if attempt.is_passed():
        user_profile.quizzes_passed += 1
    
    # Mettre à jour la série
    today = timezone.now().date()
    if user_profile.last_activity and user_profile.last_activity.date() == today:
        pass  # Déjà compté aujourd'hui
    elif user_profile.last_activity and (today - user_profile.last_activity.date()).days == 1:
        user_profile.current_streak += 1
    else:
        user_profile.current_streak = 1
    
    user_profile.longest_streak = max(user_profile.longest_streak, user_profile.current_streak)
    user_profile.last_activity = timezone.now()
    
    # Recalculer le niveau
    user_profile.level = user_profile.calculate_level()
    
    # Recalculer la moyenne
    all_attempts = QuizAttempt.objects.filter(student=request.user, status='completed')
    if all_attempts.exists():
        user_profile.average_score = all_attempts.aggregate(avg=Avg('percentage'))['avg']
    
    user_profile.save()
    
    # Vérifier et attribuer des badges
    badge_awarder = BadgeAwarder()
    awarded_badges = badge_awarder.check_and_award_badges(user_profile)
    
    # Mettre à jour les statistiques du quiz
    quiz = attempt.quiz
    quiz.total_attempts += 1
    quiz_attempts = QuizAttempt.objects.filter(quiz=quiz, status='completed')
    if quiz_attempts.exists():
        quiz.average_score = quiz_attempts.aggregate(avg=Avg('percentage'))['avg']
    quiz.save()
    
    return JsonResponse({
        'success': True,
        'score': score,
        'percentage': percentage,
        'points_earned': points_earned,
        'experience_earned': attempt.experience_earned,
        'passed': attempt.is_passed(),
        'awarded_badges': [{'name': badge.name, 'description': badge.description} for badge in awarded_badges]
    })


@login_required
def quiz_results(request, attempt_id):
    """Résultats d'un quiz"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    questions = attempt.quiz.questions.filter(is_active=True).order_by('order')
    
    # Préparer les données des questions avec les réponses
    questions_data = []
    for question in questions:
        question_id = str(question.id)
        user_answer = attempt.answers.get(question_id, '')
        is_correct = user_answer == question.correct_answer
        
        questions_data.append({
            'question': question,
            'user_answer': user_answer,
            'correct_answer': question.correct_answer,
            'is_correct': is_correct,
            'points': question.points if is_correct else 0
        })
    
    context = {
        'attempt': attempt,
        'questions_data': questions_data,
        'quiz': attempt.quiz,
    }
    
    return render(request, 'gamification/quiz_results.html', context)


@login_required
def my_profile(request):
    """Profil de gamification de l'utilisateur"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Récupérer les badges
    user_badges = UserBadge.objects.filter(user=request.user).order_by('-earned_at')
    
    # Récupérer les tentatives récentes
    recent_attempts = QuizAttempt.objects.filter(student=request.user).order_by('-started_at')[:10]
    
    # Récupérer les réalisations
    user_achievements = UserAchievement.objects.filter(user=request.user).order_by('-earned_at')
    
    # Statistiques par matière
    subject_stats = {}
    for subject in Subject.objects.filter(is_active=True):
        attempts = QuizAttempt.objects.filter(
            student=request.user,
            quiz__subject=subject,
            status='completed'
        )
        if attempts.exists():
            subject_stats[subject] = {
                'attempts': attempts.count(),
                'average_score': attempts.aggregate(avg=Avg('percentage'))['avg'],
                'passed': attempts.filter(percentage__gte=70).count()
            }
    
    context = {
        'user_profile': user_profile,
        'user_badges': user_badges,
        'recent_attempts': recent_attempts,
        'user_achievements': user_achievements,
        'subject_stats': subject_stats,
    }
    
    return render(request, 'gamification/my_profile.html', context)


def leaderboard(request):
    """Classement global"""
    leaderboard_manager = LeaderboardManager()
    
    # Classement global
    global_leaderboard = leaderboard_manager.get_global_leaderboard(limit=20)
    
    # Classements par matière
    subject_leaderboards = {}
    for subject in Subject.objects.filter(is_active=True):
        subject_leaderboards[subject] = leaderboard_manager.get_subject_leaderboard(subject, limit=10)
    
    context = {
        'global_leaderboard': global_leaderboard,
        'subject_leaderboards': subject_leaderboards,
    }
    
    return render(request, 'gamification/leaderboard.html', context)


def badges_gallery(request):
    """Galerie des badges disponibles"""
    badges = Badge.objects.filter(is_active=True).order_by('rarity', 'name')
    
    # Grouper par rareté
    badges_by_rarity = {}
    for badge in badges:
        rarity = badge.get_rarity_display()
        if rarity not in badges_by_rarity:
            badges_by_rarity[rarity] = []
        badges_by_rarity[rarity].append(badge)
    
    context = {
        'badges_by_rarity': badges_by_rarity,
    }
    
    return render(request, 'gamification/badges_gallery.html', context)


@login_required
def my_badges(request):
    """Badges obtenus par l'utilisateur"""
    user_badges = UserBadge.objects.filter(user=request.user).order_by('-earned_at')
    
    # Grouper par rareté
    badges_by_rarity = {}
    for user_badge in user_badges:
        rarity = user_badge.badge.get_rarity_display()
        if rarity not in badges_by_rarity:
            badges_by_rarity[rarity] = []
        badges_by_rarity[rarity].append(user_badge)
    
    context = {
        'badges_by_rarity': badges_by_rarity,
    }
    
    return render(request, 'gamification/my_badges.html', context)


def subject_detail(request, slug):
    """Détails d'une matière"""
    subject = get_object_or_404(Subject, slug=slug, is_active=True)
    quizzes = Quiz.objects.filter(subject=subject, status='published').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(quizzes, 12)
    page_number = request.GET.get('page')
    quizzes_page = paginator.get_page(page_number)
    
    context = {
        'subject': subject,
        'quizzes_page': quizzes_page,
    }
    
    return render(request, 'gamification/subject_detail.html', context)


@login_required
def my_attempts(request):
    """Historique des tentatives de l'utilisateur"""
    attempts = QuizAttempt.objects.filter(student=request.user).order_by('-started_at')
    
    # Pagination
    paginator = Paginator(attempts, 20)
    page_number = request.GET.get('page')
    attempts_page = paginator.get_page(page_number)
    
    context = {
        'attempts_page': attempts_page,
    }
    
    return render(request, 'gamification/my_attempts.html', context)