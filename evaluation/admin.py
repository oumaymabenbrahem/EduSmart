from django.contrib import admin
from .models import Evaluation, Question


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'start_date', 'end_date', 'is_published')
    search_fields = ('title',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'question_type', 'text')
    search_fields = ('text',)
