from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator
import json
import random
import string

from .models import (
    Quiz, QuizAttempt, Question, QuizRoom, RoomParticipant, RoomResult,
    UserProfile, Badge, UserBadge, DifficultyLevel, Subject
)
from .ai_quiz_generator import AIQuizGenerator, BadgeAwarder


def is_teacher(user):
    """Vérifie si l'utilisateur est un enseignant"""
    return user.is_authenticated and user.user_type == 'teacher'


# ==================== VUES ENSEIGNANT ====================

@login_required
@user_passes_test(is_teacher)
def teacher_room_dashboard(request):
    """Tableau de bord des rooms pour l'enseignant"""
    rooms = QuizRoom.objects.filter(teacher=request.user).order_by('-created_at')
    
    # Statistiques
    total_rooms = rooms.count()
    active_rooms = rooms.filter(status='active').count()
    total_participants = RoomParticipant.objects.filter(room__teacher=request.user).count()
    
    # Pagination
    paginator = Paginator(rooms, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'rooms': page_obj,
        'total_rooms': total_rooms,
        'active_rooms': active_rooms,
        'total_participants': total_participants,
    }
    
    return render(request, 'gamification/teacher/room_dashboard.html', context)


@login_required
@user_passes_test(is_teacher)
def create_room(request):
    """Créer une nouvelle room de quiz"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        quiz_id = request.POST.get('quiz_id')
        max_participants = int(request.POST.get('max_participants', 50))
        time_limit_override = request.POST.get('time_limit_override')
        scheduled_start = request.POST.get('scheduled_start')
        scheduled_end = request.POST.get('scheduled_end')
        
        # Options
        show_results_immediately = request.POST.get('show_results_immediately') == 'on'
        allow_review = request.POST.get('allow_review') == 'on'
        show_leaderboard = request.POST.get('show_leaderboard') == 'on'
        enable_badges = request.POST.get('enable_badges') == 'on'
        
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            
            # Créer la room
            room = QuizRoom.objects.create(
                title=title,
                description=description,
                teacher=request.user,
                quiz=quiz,
                max_participants=max_participants,
                time_limit_override=int(time_limit_override) if time_limit_override else None,
                scheduled_start=scheduled_start if scheduled_start else None,
                scheduled_end=scheduled_end if scheduled_end else None,
                show_results_immediately=show_results_immediately,
                allow_review=allow_review,
                show_leaderboard=show_leaderboard,
                enable_badges=enable_badges,
            )
            
            messages.success(request, f'Room "{room.title}" créée avec succès ! Code: {room.room_code}')
            return redirect('gamification:room_detail_teacher', room_code=room.room_code)
            
        except Quiz.DoesNotExist:
            messages.error(request, 'Quiz non trouvé.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la room: {str(e)}')
    
    # GET request - afficher le formulaire
    quizzes = Quiz.objects.filter(
        Q(created_by=request.user) | Q(status='published')
    ).order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
    }
    
    return render(request, 'gamification/teacher/create_room.html', context)


@login_required
@user_passes_test(is_teacher)
def create_room_with_ai_quiz(request):
    """Créer une room avec un quiz généré par IA"""
    if request.method == 'POST':
        # Informations de la room
        room_title = request.POST.get('room_title')
        room_description = request.POST.get('room_description', '')
        
        # Paramètres du quiz IA
        subject_name = request.POST.get('subject')
        difficulty_level = int(request.POST.get('difficulty', 3))
        num_questions = int(request.POST.get('num_questions', 15))
        quiz_title = request.POST.get('quiz_title')
        
        # Configuration de la room
        max_participants = int(request.POST.get('max_participants', 50))
        time_limit = int(request.POST.get('time_limit', 30))
        
        try:
            # Générer le quiz avec IA
            generator = AIQuizGenerator()
            
            # Créer un profil temporaire pour la génération
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            
            quiz = generator.generate_quiz(
                subject_name=subject_name,
                difficulty_level=difficulty_level,
                num_questions=num_questions,
                user_profile=user_profile
            )
            
            if quiz:
                # Mettre à jour le titre du quiz si fourni
                if quiz_title:
                    quiz.title = quiz_title
                    quiz.save()
                
                # Créer la room avec le quiz généré
                room = QuizRoom.objects.create(
                    title=room_title,
                    description=room_description,
                    teacher=request.user,
                    quiz=quiz,
                    max_participants=max_participants,
                    time_limit_override=time_limit,
                    show_results_immediately=True,
                    allow_review=True,
                    show_leaderboard=True,
                    enable_badges=True,
                )
                
                messages.success(
                    request, 
                    f'Room "{room.title}" créée avec un quiz IA de {num_questions} questions ! Code: {room.room_code}'
                )
                return redirect('gamification:room_detail_teacher', room_code=room.room_code)
            else:
                messages.error(request, 'Erreur lors de la génération du quiz IA.')
                
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    # GET request
    from .models import Subject
    subjects = Subject.objects.filter(is_active=True)
    difficulty_levels = DifficultyLevel.objects.all()
    
    context = {
        'subjects': subjects,
        'difficulty_levels': difficulty_levels,
    }
    
    return render(request, 'gamification/teacher/create_room_ai.html', context)


@login_required
@user_passes_test(is_teacher)
def room_detail_teacher(request, room_code):
    """Détails d'une room pour l'enseignant"""
    room = get_object_or_404(QuizRoom, room_code=room_code, teacher=request.user)
    participants = room.participants.all().order_by('-joined_at')
    
    # Statistiques
    completed_count = participants.filter(status='completed').count()
    in_progress_count = participants.filter(status='in_progress').count()
    
    # Résultats
    results = RoomResult.objects.filter(
        participant__room=room
    ).select_related('participant__student').order_by('rank')
    
    context = {
        'room': room,
        'participants': participants,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'results': results,
    }
    
    return render(request, 'gamification/teacher/room_detail.html', context)


@login_required
@user_passes_test(is_teacher)
def start_room(request, room_code):
    """Démarrer une room"""
    room = get_object_or_404(QuizRoom, room_code=room_code, teacher=request.user)
    
    if room.status == 'waiting':
        room.start_room()
        messages.success(request, f'Room "{room.title}" démarrée !')
    else:
        messages.warning(request, 'Cette room est déjà démarrée ou terminée.')
    
    return redirect('gamification:room_detail_teacher', room_code=room_code)


@login_required
@user_passes_test(is_teacher)
def end_room(request, room_code):
    """Terminer une room"""
    room = get_object_or_404(QuizRoom, room_code=room_code, teacher=request.user)
    
    if room.status == 'active':
        room.end_room()
        messages.success(request, f'Room "{room.title}" terminée !')
    else:
        messages.warning(request, 'Cette room n\'est pas active.')
    
    return redirect('gamification:room_detail_teacher', room_code=room_code)


@login_required
@user_passes_test(is_teacher)
def delete_room(request, room_code):
    """Supprimer une room"""
    room = get_object_or_404(QuizRoom, room_code=room_code, teacher=request.user)
    
    if request.method == 'POST':
        room_title = room.title
        room.delete()
        messages.success(request, f'Room "{room_title}" supprimée avec succès.')
        return redirect('gamification:teacher_room_dashboard')
    
    return redirect('gamification:room_detail_teacher', room_code=room_code)


# ==================== VUES ÉTUDIANT ====================

@login_required
def student_room_list(request):
    """Liste des rooms pour l'étudiant"""
    # Rooms auxquelles l'étudiant participe
    my_rooms = RoomParticipant.objects.filter(
        student=request.user
    ).select_related('room', 'room__quiz').order_by('-joined_at')
    
    context = {
        'my_rooms': my_rooms,
    }
    
    return render(request, 'gamification/student/room_list.html', context)


@login_required
def join_room(request):
    """Rejoindre une room avec un code"""
    if request.method == 'POST':
        room_code = request.POST.get('room_code', '').strip().upper()
        
        try:
            room = QuizRoom.objects.get(room_code=room_code)
            
            # Vérifier si l'étudiant peut rejoindre
            if not room.can_join():
                if room.status == 'completed':
                    messages.error(request, 'Cette room est terminée.')
                elif room.status == 'cancelled':
                    messages.error(request, 'Cette room a été annulée.')
                else:
                    messages.error(request, 'Cette room est pleine.')
                return redirect('gamification:student_room_list')
            
            # Vérifier si déjà participant
            participant, created = RoomParticipant.objects.get_or_create(
                room=room,
                student=request.user
            )
            
            if created:
                # Mettre à jour le compteur de participants
                room.total_participants = room.participants.count()
                room.save()
                
                messages.success(request, f'Vous avez rejoint la room "{room.title}" !')
            else:
                messages.info(request, f'Vous êtes déjà dans la room "{room.title}".')
            
            return redirect('gamification:room_detail_student', room_code=room_code)
            
        except QuizRoom.DoesNotExist:
            messages.error(request, 'Code de room invalide.')

    return render(request, 'gamification/student/join_room.html')


@login_required
def room_detail_student(request, room_code):
    """Détails d'une room pour l'étudiant"""
    room = get_object_or_404(QuizRoom, room_code=room_code)

    # Vérifier si l'étudiant est participant
    try:
        participant = RoomParticipant.objects.get(room=room, student=request.user)
    except RoomParticipant.DoesNotExist:
        messages.error(request, 'Vous devez rejoindre cette room d\'abord.')
        return redirect('gamification:join_room')

    # Vérifier s'il y a un résultat
    try:
        result = RoomResult.objects.get(participant=participant)
    except RoomResult.DoesNotExist:
        result = None

    context = {
        'room': room,
        'participant': participant,
        'result': result,
    }

    return render(request, 'gamification/student/room_detail.html', context)


@login_required
def start_room_quiz(request, room_code):
    """Démarrer le quiz d'une room"""
    room = get_object_or_404(QuizRoom, room_code=room_code)

    # Vérifier si l'étudiant est participant
    try:
        participant = RoomParticipant.objects.get(room=room, student=request.user)
    except RoomParticipant.DoesNotExist:
        messages.error(request, 'Vous devez rejoindre cette room d\'abord.')
        return redirect('gamification:join_room')

    # Vérifier si le quiz n'a pas déjà été commencé
    if participant.status != 'joined':
        messages.warning(request, 'Vous avez déjà commencé ce quiz.')
        return redirect('gamification:take_room_quiz', room_code=room_code)

    # Vérifier si la room est active
    if room.status != 'active':
        messages.error(request, 'Cette room n\'est pas encore active.')
        return redirect('gamification:room_detail_student', room_code=room_code)

    # Créer une tentative de quiz
    attempt_number = QuizAttempt.objects.filter(
        student=request.user,
        quiz=room.quiz
    ).count() + 1

    quiz_attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=room.quiz,
        attempt_number=attempt_number,
        status='in_progress'
    )

    # Lier la tentative au participant
    participant.quiz_attempt = quiz_attempt
    participant.start_quiz()

    messages.success(request, 'Quiz démarré ! Bonne chance !')
    return redirect('gamification:take_room_quiz', room_code=room_code)


@login_required
def take_room_quiz(request, room_code):
    """Passer le quiz d'une room"""
    room = get_object_or_404(QuizRoom, room_code=room_code)

    # Vérifier si l'étudiant est participant
    try:
        participant = RoomParticipant.objects.get(room=room, student=request.user)
    except RoomParticipant.DoesNotExist:
        messages.error(request, 'Vous devez rejoindre cette room d\'abord.')
        return redirect('gamification:join_room')

    # Vérifier s'il y a une tentative en cours
    if not participant.quiz_attempt or participant.status == 'completed':
        messages.error(request, 'Aucun quiz en cours.')
        return redirect('gamification:room_detail_student', room_code=room_code)

    quiz_attempt = participant.quiz_attempt
    questions = room.quiz.questions.filter(is_active=True).order_by('order')

    # Calculer le temps restant
    time_limit = room.get_time_limit()
    elapsed_time = (timezone.now() - quiz_attempt.started_at).total_seconds()
    time_remaining = max(0, (time_limit * 60) - elapsed_time)

    context = {
        'room': room,
        'quiz': room.quiz,
        'questions': questions,
        'quiz_attempt': quiz_attempt,
        'time_remaining': int(time_remaining),
        'participant': participant,
    }

    return render(request, 'gamification/student/take_quiz.html', context)


@login_required
@require_http_methods(["POST"])
def submit_room_quiz(request, room_code):
    """Soumettre les réponses du quiz"""
    room = get_object_or_404(QuizRoom, room_code=room_code)

    # Vérifier si l'étudiant est participant
    try:
        participant = RoomParticipant.objects.get(room=room, student=request.user)
    except RoomParticipant.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Participant non trouvé'})

    quiz_attempt = participant.quiz_attempt
    if not quiz_attempt:
        return JsonResponse({'success': False, 'error': 'Aucune tentative en cours'})

    try:
        # Récupérer les réponses
        data = json.loads(request.body)
        answers = data.get('answers', {})

        # Calculer le score
        questions = room.quiz.questions.filter(is_active=True)
        total_points = 0
        earned_points = 0
        correct_count = 0
        wrong_count = 0
        skipped_count = 0

        easy_correct = 0
        medium_correct = 0
        hard_correct = 0

        for question in questions:
            total_points += question.points
            question_id = str(question.id)

            if question_id in answers:
                user_answer = answers[question_id]

                if user_answer == question.correct_answer:
                    earned_points += question.points
                    correct_count += 1

                    # Compter par difficulté
                    if question.difficulty_score < 0.4:
                        easy_correct += 1
                    elif question.difficulty_score < 0.7:
                        medium_correct += 1
                    else:
                        hard_correct += 1
                else:
                    wrong_count += 1
            else:
                skipped_count += 1

        # Calculer le pourcentage
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0

        # Calculer le temps pris
        time_taken = int((timezone.now() - quiz_attempt.started_at).total_seconds())

        # Mettre à jour la tentative de quiz
        quiz_attempt.score = earned_points
        quiz_attempt.percentage = percentage
        quiz_attempt.points_earned = int(earned_points * room.quiz.difficulty.points_multiplier)
        quiz_attempt.experience_earned = int(room.quiz.experience_points * (percentage / 100))
        quiz_attempt.time_taken = time_taken
        quiz_attempt.completed_at = timezone.now()
        quiz_attempt.status = 'completed'
        quiz_attempt.answers = answers
        quiz_attempt.save()

        # Marquer le participant comme terminé
        participant.complete_quiz()

        # Créer ou mettre à jour le résultat
        result, created = RoomResult.objects.get_or_create(
            participant=participant,
            defaults={
                'score': earned_points,
                'percentage': percentage,
                'grade': room.calculate_grade(percentage),
                'correct_answers': correct_count,
                'wrong_answers': wrong_count,
                'skipped_answers': skipped_count,
                'total_questions': questions.count(),
                'time_taken': time_taken,
                'average_time_per_question': time_taken / questions.count() if questions.count() > 0 else 0,
                'points_earned': quiz_attempt.points_earned,
                'experience_earned': quiz_attempt.experience_earned,
                'easy_correct': easy_correct,
                'medium_correct': medium_correct,
                'hard_correct': hard_correct,
            }
        )

        # Calculer le classement
        result.calculate_rank()

        # Mettre à jour le profil utilisateur
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_profile.total_points += quiz_attempt.points_earned
        user_profile.experience_points += quiz_attempt.experience_earned
        user_profile.quizzes_completed += 1
        if percentage >= room.quiz.passing_score:
            user_profile.quizzes_passed += 1
        user_profile.total_attempts += 1

        # Recalculer le score moyen
        all_attempts = QuizAttempt.objects.filter(student=request.user, status='completed')
        user_profile.average_score = all_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0

        # Mettre à jour le niveau
        user_profile.level = user_profile.calculate_level()
        user_profile.last_activity = timezone.now()
        user_profile.save()

        # Attribuer des badges si activé
        awarded_badges = []
        if room.enable_badges:
            badge_awarder = BadgeAwarder()
            awarded_badges = badge_awarder.check_and_award_badges(user_profile)

            # Ajouter les badges au résultat
            for badge in awarded_badges:
                result.badges_earned.add(badge)

        # Mettre à jour les statistiques de la room
        room.completed_participants = room.participants.filter(status='completed').count()
        completed_results = RoomResult.objects.filter(participant__room=room)
        room.average_score = completed_results.aggregate(Avg('percentage'))['percentage__avg'] or 0
        room.save()

        return JsonResponse({
            'success': True,
            'score': earned_points,
            'percentage': round(percentage, 2),
            'grade': result.grade,
            'rank': result.rank,
            'badges_earned': [{'name': b.name, 'icon': b.icon, 'color': b.color} for b in awarded_badges],
            'redirect_url': f'/gamification/room/{room_code}/result/'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def room_result(request, room_code):
    """Afficher les résultats du quiz de la room"""
    room = get_object_or_404(QuizRoom, room_code=room_code)

    # Vérifier si l'étudiant est participant
    try:
        participant = RoomParticipant.objects.get(room=room, student=request.user)
    except RoomParticipant.DoesNotExist:
        messages.error(request, 'Vous devez rejoindre cette room d\'abord.')
        return redirect('gamification:join_room')

    # Récupérer le résultat
    try:
        result = RoomResult.objects.get(participant=participant)
    except RoomResult.DoesNotExist:
        messages.error(request, 'Aucun résultat disponible.')
        return redirect('gamification:room_detail_student', room_code=room_code)

    # Récupérer le classement si activé
    leaderboard = None
    if room.show_leaderboard:
        leaderboard = RoomResult.objects.filter(
            participant__room=room
        ).select_related('participant__student').order_by('rank')[:10]

    # Récupérer les détails des réponses si la révision est autorisée
    quiz_details = None
    if room.allow_review and participant.quiz_attempt:
        questions = room.quiz.questions.filter(is_active=True).order_by('order')
        quiz_details = []

        for question in questions:
            user_answer = participant.quiz_attempt.answers.get(str(question.id), None)
            is_correct = user_answer == question.correct_answer

            quiz_details.append({
                'question': question,
                'user_answer': user_answer,
                'is_correct': is_correct,
            })

    context = {
        'room': room,
        'participant': participant,
        'result': result,
        'leaderboard': leaderboard,
        'quiz_details': quiz_details,
    }

    return render(request, 'gamification/student/room_result.html', context)


@login_required
def room_leaderboard(request, room_code):
    """Afficher le classement complet de la room"""
    room = get_object_or_404(QuizRoom, room_code=room_code)

    if not room.show_leaderboard:
        messages.error(request, 'Le classement n\'est pas disponible pour cette room.')
        return redirect('gamification:room_detail_student', room_code=room_code)

    # Récupérer tous les résultats
    results = RoomResult.objects.filter(
        participant__room=room
    ).select_related('participant__student').order_by('rank')

    context = {
        'room': room,
        'results': results,
    }

    return render(request, 'gamification/student/room_leaderboard.html', context)

