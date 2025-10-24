from django.db import models
from django.conf import settings
from django.utils import timezone


class Evaluation(models.Model):
    TYPE_CHOICES = [
        ('qcm', 'QCM'),
        ('open', 'Réponse ouverte'),
        ('practical', 'Exercice pratique'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        """Vérifie si l'évaluation est disponible pour les étudiants"""
        now = timezone.now()
        if not self.is_published:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    @property
    def total_points(self):
        """Calcule le total des points de l'évaluation"""
        return sum(question.points for question in self.questions.all())

    @property
    def questions_count(self):
        """Retourne le nombre de questions"""
        return self.questions.count()


class Question(models.Model):
    QUESTION_TYPE = [
        ('qcm', 'QCM'),
        ('open', 'Réponse ouverte'),
        ('practical', 'Exercice pratique'),
    ]

    evaluation = models.ForeignKey(Evaluation, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE, default='qcm')
    choices = models.JSONField(null=True, blank=True, help_text='JSON list of choices for QCM')
    correct_answer = models.TextField(null=True, blank=True)
    points = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.evaluation.title} - {self.text[:40]}"


class StudentResponse(models.Model):
    """Modèle pour stocker les réponses des étudiants aux évaluations"""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField()  # Réponse de l'étudiant
    is_correct = models.BooleanField(null=True, blank=True)  # Pour QCM uniquement
    points_earned = models.IntegerField(default=0)  # Points obtenus
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'evaluation', 'question']

    def __str__(self):
        return f"{self.student.username} - {self.evaluation.title} - {self.question.text[:30]}"


class EvaluationAttempt(models.Model):
    """Modèle pour suivre les tentatives d'évaluation des étudiants"""

    STATUS_CHOICES = [
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('timed_out', 'Expirée'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)

    class Meta:
        unique_together = ['student', 'evaluation']

    def __str__(self):
        return f"{self.student.username} - {self.evaluation.title} ({self.status})"

    @property
    def score_percentage(self):
        """Calcule le pourcentage de score"""
        if self.max_score == 0:
            return 0
        return round((self.total_score / self.max_score) * 100, 1)

    @property
    def time_elapsed(self):
        """Calcule le temps écoulé"""
        end_time = self.completed_at or timezone.now()
        elapsed = end_time - self.started_at
        return elapsed

    def calculate_score(self):
        """Calcule le score total basé sur les réponses"""
        responses = StudentResponse.objects.filter(
            student=self.student,
            evaluation=self.evaluation
        )
        self.total_score = sum(response.points_earned for response in responses)
        self.max_score = self.evaluation.total_points
        self.save()
