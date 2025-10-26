from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .forms import EvaluationForm, QuestionFormSet
from .ai_feedback_generator import generate_student_feedback
from .models import Evaluation, StudentResponse, EvaluationAttempt, AIFeedback




def _is_teacher(user):
    return user.is_authenticated and getattr(user, 'user_type', None) == 'teacher'


@login_required
def dashboard(request):
    """Vue simple du tableau de bord de gestion des évaluations"""
    # Rediriger vers la liste unifiée des évaluations pour tous les utilisateurs
    return redirect('evaluation:list')


@login_required
def create_evaluation(request):
    """Page principale des évaluations - Création pour enseignants, vue des évaluations pour étudiants"""
    # Rediriger les étudiants vers le tableau de bord
    if request.user.user_type != 'teacher':
        return redirect('evaluation:dashboard')

    # Vérifier si on est en mode édition
    edit_id = request.GET.get('edit')
    evaluation = None
    if edit_id:
        evaluation = get_object_or_404(Evaluation, id=edit_id, created_by=request.user)

    # Gestion du formulaire pour les enseignants
    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=evaluation)
        formset = QuestionFormSet(request.POST, instance=evaluation)

        if form.is_valid() and formset.is_valid():
            evaluation = form.save(commit=False)
            evaluation.created_by = request.user
            evaluation.save()
            formset.instance = evaluation
            formset.save()
            messages.success(request, "Évaluation sauvegardée avec succès !")
            # Rediriger vers la liste des évaluations après sauvegarde
            return redirect('evaluation:list')
    else:
        form = EvaluationForm(instance=evaluation)
        formset = QuestionFormSet(instance=evaluation)

    title = 'Modifier l\'évaluation' if evaluation else 'Nouvelle évaluation'

    return render(request, 'evaluation/create.html', {
        'form': form,
        'formset': formset,
        'title': title,
        'evaluation': evaluation,
        'is_edit': evaluation is not None
    })


@login_required
def student_evaluations(request):
    """Vue pour les étudiants - Liste des évaluations disponibles"""
    if request.user.user_type == 'teacher':
        return redirect('evaluation:create')

    # Récupérer les évaluations disponibles
    now = timezone.now()
    available_evaluations = Evaluation.objects.filter(
        is_published=True,
        start_date__lte=now
    ).exclude(
        end_date__lt=now
    )

    # Récupérer les tentatives de l'étudiant
    student_attempts = EvaluationAttempt.objects.filter(student=request.user)

    # Créer un dictionnaire des tentatives par évaluation
    attempts_dict = {attempt.evaluation_id: attempt for attempt in student_attempts}

    # Préparer les données pour le template
    evaluations_data = []
    for evaluation in available_evaluations:
        attempt = attempts_dict.get(evaluation.id)
        evaluations_data.append({
            'evaluation': evaluation,
            'attempt': attempt,
            'can_take': attempt is None or attempt.status == 'in_progress',
            'is_completed': attempt.status == 'completed' if attempt else False,
        })

    return render(request, 'evaluation/student_list.html', {
        'evaluations_data': evaluations_data,
        'title': 'Mes Évaluations'
    })


@login_required
def take_evaluation(request, evaluation_id):
    """Vue pour passer une évaluation"""
    if request.user.user_type == 'teacher':
        return redirect('evaluation:create')

    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    # Vérifier si l'évaluation est disponible
    now = timezone.now()
    if not (evaluation.is_published and evaluation.start_date <= now and (evaluation.end_date is None or evaluation.end_date >= now)):
        messages.error(request, "Cette évaluation n'est pas disponible actuellement.")
        return redirect('evaluation:student_list')

    # Récupérer ou créer la tentative
    attempt, created = EvaluationAttempt.objects.get_or_create(
        student=request.user,
        evaluation=evaluation,
        defaults={'status': 'in_progress'}
    )

    if attempt.status == 'completed':
        messages.info(request, "Vous avez déjà terminé cette évaluation.")
        return redirect('evaluation:results', evaluation_id=evaluation_id)

    questions = evaluation.questions.all().order_by('id')

    if request.method == 'POST':
        # Traiter les réponses soumises
        for question in questions:
            answer_key = f'question_{question.id}'
            if answer_key in request.POST:
                answer = request.POST[answer_key].strip()

                # Calculer si la réponse est correcte et les points
                is_correct = None
                points_earned = 0

                if question.question_type == 'qcm':
                    is_correct = answer == question.correct_answer
                    points_earned = question.points if is_correct else 0
                else:
                    # Pour les questions ouvertes et pratiques, on stocke juste la réponse
                    # La correction sera faite manuellement par l'enseignant
                    points_earned = 0

                # Sauvegarder ou mettre à jour la réponse
                response, created = StudentResponse.objects.update_or_create(
                    student=request.user,
                    evaluation=evaluation,
                    question=question,
                    defaults={
                        'answer': answer,
                        'is_correct': is_correct,
                        'points_earned': points_earned
                    }
                )

        # Marquer l'évaluation comme terminée
        attempt.status = 'completed'
        attempt.completed_at = timezone.now()
        attempt.calculate_score()
        attempt.save()

        messages.success(request, f"Évaluation terminée ! Votre score : {attempt.total_score}/{attempt.max_score} points ({attempt.score_percentage}%)")
        return redirect('evaluation:results', evaluation_id=evaluation_id)

    # Récupérer les réponses existantes
    existing_responses = StudentResponse.objects.filter(
        student=request.user,
        evaluation=evaluation
    )
    responses_dict = {response.question_id: response for response in existing_responses}

    return render(request, 'evaluation/take.html', {
        'evaluation': evaluation,
        'questions': questions,
        'responses_dict': responses_dict,
        'attempt': attempt,
        'title': f'Évaluation : {evaluation.title}'
    })


@login_required
def evaluations_list(request):
    """Vue unifiée pour afficher la liste des évaluations selon le rôle de l'utilisateur"""
    if request.user.user_type == 'teacher':
        # Enseignants voient seulement leurs propres évaluations
        evaluations = Evaluation.objects.filter(created_by=request.user).order_by('-created_at')
        is_teacher = True
    else:
        # Étudiants voient seulement les évaluations disponibles
        now = timezone.now()
        evaluations = Evaluation.objects.filter(
            is_published=True,
            start_date__lte=now
        ).exclude(
            end_date__lt=now
        ).order_by('-created_at')

        # Récupérer les tentatives de l'étudiant
        student_attempts = EvaluationAttempt.objects.filter(student=request.user)
        attempts_dict = {attempt.evaluation_id: attempt for attempt in student_attempts}
        is_teacher = False

    # Préparer les données pour le template
    evaluations_data = []
    for evaluation in evaluations:
        if is_teacher:
            # Pour les enseignants, pas de logique de tentatives
            evaluations_data.append({
                'evaluation': evaluation,
                'is_teacher': True,
            })
        else:
            # Pour les étudiants, inclure les informations de tentative
            attempt = attempts_dict.get(evaluation.id)
            evaluations_data.append({
                'evaluation': evaluation,
                'attempt': attempt,
                'can_take': attempt is None or attempt.status == 'in_progress',
                'is_completed': attempt.status == 'completed' if attempt else False,
                'is_teacher': False,
            })

    return render(request, 'evaluation/list.html', {
        'evaluations_data': evaluations_data,
        'is_teacher': is_teacher,
        'title': 'Évaluations'
    })


@login_required
@user_passes_test(_is_teacher)
def delete_evaluation(request, evaluation_id):
    """Vue pour supprimer une évaluation (enseignants uniquement)"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, created_by=request.user)

    if request.method == 'POST':
        evaluation_title = evaluation.title
        evaluation.delete()
        messages.success(request, f"L'évaluation '{evaluation_title}' a été supprimée avec succès.")
        return redirect('evaluation:list')

    # Si ce n'est pas une requête POST, rediriger vers la liste
    return redirect('evaluation:list')
    
@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'user_type', None) == 'admin')
def admin_evaluations_list(request):
    """Vue pour afficher et gérer toutes les évaluations dans l'espace admin"""
    evaluations = Evaluation.objects.all().select_related('created_by').order_by('-created_at')
    return render(request, 'evaluation/admin_list.html', {
        'evaluations': evaluations,
        'title': 'Gestion des Évaluations'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'user_type', None) == 'admin')
def admin_evaluation_edit(request, evaluation_id):
    """Vue pour modifier une évaluation dans l'espace admin"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            messages.success(request, "Évaluation modifiée avec succès.")
            return redirect('evaluation:admin_list')
    else:
        form = EvaluationForm(instance=evaluation)

    return render(request, 'evaluation/admin_edit.html', {
        'form': form,
        'evaluation': evaluation,
        'title': f'Modifier : {evaluation.title}'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'user_type', None) == 'admin')
def admin_evaluation_delete(request, evaluation_id):
    """Vue pour supprimer une évaluation dans l'espace admin"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    if request.method == 'POST':
        evaluation.delete()
        messages.success(request, "Évaluation supprimée avec succès.")
        return redirect('evaluation:admin_list')

    return render(request, 'evaluation/admin_delete.html', {
        'evaluation': evaluation,
        'title': f'Supprimer : {evaluation.title}'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'user_type', None) == 'admin')
def admin_evaluation_details(request, evaluation_id):
    """Vue pour afficher les détails d'une évaluation dans l'espace admin"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    questions = evaluation.questions.all().order_by('id')
    attempts = evaluation.evaluationattempt_set.all().select_related('student').order_by('-completed_at')

    # Statistiques
    total_attempts = attempts.count()
    completed_attempts = attempts.filter(status='completed').count()
    average_score = 0
    if completed_attempts > 0:
        total_scores = sum(attempt.score_percentage for attempt in attempts.filter(status='completed'))
        average_score = total_scores / completed_attempts

    context = {
        'evaluation': evaluation,
        'questions': questions,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'completed_attempts': completed_attempts,
        'average_score': round(average_score, 1),
        'title': f'Détails : {evaluation.title}'
    }

    return render(request, 'evaluation/admin_details.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or getattr(u, 'user_type', None) == 'admin')
def admin_evaluation_toggle_publish(request, evaluation_id):
    """Vue pour publier/dépublier une évaluation dans l'espace admin"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    evaluation.is_published = not evaluation.is_published
    evaluation.save()
    status = "publiée" if evaluation.is_published else "dépubliée"
    messages.success(request, f"Évaluation {status} avec succès.")
    return redirect('evaluation:admin_list')


@login_required
def evaluation_results(request, evaluation_id):
    """Vue pour afficher les résultats d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    try:
        attempt = EvaluationAttempt.objects.get(
            student=request.user,
            evaluation=evaluation,
            status='completed'
        )
    except EvaluationAttempt.DoesNotExist:
        messages.error(request, "Vous n'avez pas encore terminé cette évaluation.")
        return redirect('evaluation:student_list')

    # Récupérer toutes les réponses de l'étudiant
    responses = StudentResponse.objects.filter(
        student=request.user,
        evaluation=evaluation
    ).select_related('question')

    return render(request, 'evaluation/results.html', {
        'evaluation': evaluation,
        'attempt': attempt,
        'responses': responses,
        'title': f'Résultats : {evaluation.title}'
    })


@login_required
def generate_ai_feedback(request, evaluation_id):
    """Vue pour générer et afficher le feedback IA pour une évaluation"""
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    try:
        attempt = EvaluationAttempt.objects.get(
            student=request.user,
            evaluation=evaluation,
            status='completed'
        )
    except EvaluationAttempt.DoesNotExist:
        messages.error(request, "Vous n'avez pas encore terminé cette évaluation.")
        return redirect('evaluation:student_list')

    # Vérifier si le feedback IA existe déjà
    ai_feedback, created = AIFeedback.objects.get_or_create(
        student=request.user,
        evaluation=evaluation,
        defaults={'feedback_text': '', 'generated_at': timezone.now()}
    )

    if created or not ai_feedback.feedback_text:
        # Générer le feedback si nouveau ou vide
        try:
            feedback_text = generate_student_feedback(attempt)
            ai_feedback.feedback_text = feedback_text
            ai_feedback.generated_at = timezone.now()
            ai_feedback.save()
            messages.success(request, "Feedback IA généré avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du feedback : {str(e)}")
            return redirect('evaluation:results', evaluation_id=evaluation_id)

    # Récupérer toutes les réponses de l'étudiant
    responses = StudentResponse.objects.filter(
        student=request.user,
        evaluation=evaluation
    ).select_related('question')

    return render(request, 'evaluation/ai_feedback.html', {
        'evaluation': evaluation,
        'attempt': attempt,
        'responses': responses,
        'ai_feedback': ai_feedback,
        'title': f'Feedback IA : {evaluation.title}'
    })
