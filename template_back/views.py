from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg
from gamification.models import Quiz, QuizAttempt, UserProfile, Badge
from cours.models import Course, CourseModule, CourseResource

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
