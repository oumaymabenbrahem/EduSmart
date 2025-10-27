from django.contrib import admin
from .models import Subject, Course, CourseEnrollment, CourseReview, CourseModule, CourseResource


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'level', 'status', 'instructor', 'total_views', 'total_enrollments', 'created_at']
    list_filter = ['status', 'level', 'subject', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['total_views', 'total_enrollments', 'average_rating', 'created_at', 'updated_at']
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'subject', 'level', 'description', 'content')
        }),
        ('Configuration', {
            'fields': ('instructor', 'status', 'is_active', 'duration_hours', 'difficulty_score')
        }),
        ('Objectifs et prérequis', {
            'fields': ('objectives', 'prerequisites')
        }),
        ('Médias', {
            'fields': ('thumbnail', 'video_url')
        }),
        ('Statistiques', {
            'fields': ('total_views', 'total_enrollments', 'average_rating'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'progress_percentage', 'enrolled_at', 'completed_at']
    list_filter = ['status', 'enrolled_at', 'completed_at']
    search_fields = ['student__username', 'course__title']
    readonly_fields = ['enrolled_at']


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['student__username', 'course__title', 'comment']
    readonly_fields = ['created_at']


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'order', 'is_active']
    list_filter = ['is_active', 'course']
    search_fields = ['title', 'description', 'course__title']
    list_editable = ['order', 'is_active']


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ['course', 'module', 'title', 'resource_type', 'is_active']
    list_filter = ['resource_type', 'is_active', 'course']
    search_fields = ['title', 'description', 'course__title']
    list_editable = ['is_active']
