from django.urls import path
from . import views
from . import admin_views

app_name = 'gamification'

urlpatterns = [
    # Pages principales
    path('', views.gamification_home, name='home'),
    path('select-quiz/', views.select_quiz, name='select_quiz'),
    path('generate-quiz/', views.generate_quiz, name='generate_quiz'),
    
    # Quiz
    path('quiz/<slug:slug>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<slug:slug>/start/', views.start_quiz, name='start_quiz'),
    path('quiz/attempt/<int:attempt_id>/', views.take_quiz, name='take_quiz'),
    path('quiz/attempt/<int:attempt_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    
    # Profil et statistiques
    path('my-profile/', views.my_profile, name='my_profile'),
    path('my-attempts/', views.my_attempts, name='my_attempts'),
    
    # Classements
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # Badges
    path('badges/', views.badges_gallery, name='badges_gallery'),
    path('my-badges/', views.my_badges, name='my_badges'),
    
    # Matières
    path('subject/<slug:slug>/', views.subject_detail, name='subject_detail'),
    
    # Pages admin
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/quiz-management/', admin_views.admin_quiz_management, name='admin_quiz_management'),
    path('admin/user-management/', admin_views.admin_user_management, name='admin_user_management'),
    path('admin/leaderboard-management/', admin_views.admin_leaderboard_management, name='admin_leaderboard_management'),
    path('admin/badge-management/', admin_views.admin_badge_management, name='admin_badge_management'),
    path('admin/analytics/', admin_views.admin_analytics, name='admin_analytics'),
]
