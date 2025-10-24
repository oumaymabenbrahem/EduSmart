from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Subject, DifficultyLevel, Quiz, Question, QuizAttempt,
    Badge, UserBadge, UserProfile, Leaderboard, Achievement, UserAchievement
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def color_preview(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            obj.color, obj.color
        )
    color_preview.short_description = 'Couleur'


@admin.register(DifficultyLevel)
class DifficultyLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'points_multiplier', 'color_preview']
    list_filter = ['level']
    search_fields = ['name', 'description']
    
    def color_preview(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            obj.color, obj.color
        )
    color_preview.short_description = 'Couleur'


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['question_text', 'question_type', 'correct_answer', 'points', 'order', 'is_active']
    ordering = ['order']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'difficulty', 'status', 'is_ai_generated', 'total_attempts', 'average_score', 'created_at']
    list_filter = ['status', 'is_ai_generated', 'subject', 'difficulty', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [QuestionInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'subject', 'difficulty', 'description', 'instructions')
        }),
        ('Configuration', {
            'fields': ('time_limit', 'max_attempts', 'passing_score', 'points_available', 'experience_points')
        }),
        ('IA et génération', {
            'fields': ('is_ai_generated', 'ai_prompt', 'ai_model_version'),
            'classes': ('collapse',)
        }),
        ('Statut et statistiques', {
            'fields': ('status', 'created_by', 'total_attempts', 'average_score'),
            'classes': ('collapse',)
        })
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'quiz', 'question_type', 'correct_answer', 'points', 'is_ai_generated', 'order']
    list_filter = ['question_type', 'is_ai_generated', 'quiz__subject', 'is_active']
    search_fields = ['question_text', 'quiz__title']
    ordering = ['quiz', 'order']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'attempt_number', 'score', 'percentage', 'status', 'started_at']
    list_filter = ['status', 'quiz__subject', 'started_at']
    search_fields = ['student__username', 'quiz__title']
    readonly_fields = ['started_at', 'completed_at', 'time_taken']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('student', 'quiz', 'attempt_number', 'status')
        }),
        ('Résultats', {
            'fields': ('score', 'percentage', 'points_earned', 'experience_earned')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'time_taken')
        }),
        ('Réponses', {
            'fields': ('answers',),
            'classes': ('collapse',)
        })
    )


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'rarity', 'icon', 'color_preview', 'points_reward', 'is_active']
    list_filter = ['badge_type', 'rarity', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def color_preview(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            obj.color, obj.color
        )
    color_preview.short_description = 'Couleur'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at']
    list_filter = ['badge__badge_type', 'badge__rarity', 'earned_at']
    search_fields = ['user__username', 'badge__name']
    readonly_fields = ['earned_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'total_points', 'experience_points', 'quizzes_completed', 'current_streak']
    list_filter = ['level', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Points et niveau', {
            'fields': ('total_points', 'experience_points', 'level')
        }),
        ('Statistiques', {
            'fields': ('quizzes_completed', 'quizzes_passed', 'total_attempts', 'average_score')
        }),
        ('Séries', {
            'fields': ('current_streak', 'longest_streak', 'last_activity')
        }),
        ('Préférences', {
            'fields': ('favorite_subjects', 'preferred_difficulty')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'leaderboard_type', 'subject', 'is_active', 'created_at']
    list_filter = ['leaderboard_type', 'is_active', 'created_at']
    search_fields = ['name']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'points_reward', 'experience_reward', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['earned_at']
    search_fields = ['user__username', 'achievement__name']
    readonly_fields = ['earned_at']