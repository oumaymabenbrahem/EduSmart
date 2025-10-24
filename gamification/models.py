from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class Subject(models.Model):
    """Matières disponibles pour les quiz"""
    name = models.CharField(max_length=100, verbose_name='Nom de la matière')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(max_length=50, default='bi-book', help_text='Classe d\'icône Bootstrap')
    color = models.CharField(max_length=7, default='#007bff', help_text='Couleur hexadécimale')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Matière'
        verbose_name_plural = 'Matières'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('gamification:subject_detail', kwargs={'slug': self.slug})


class DifficultyLevel(models.Model):
    """Niveaux de difficulté"""
    name = models.CharField(max_length=50, verbose_name='Nom')
    level = models.IntegerField(unique=True, verbose_name='Niveau')
    description = models.TextField(blank=True, verbose_name='Description')
    color = models.CharField(max_length=7, default='#28a745', help_text='Couleur hexadécimale')
    points_multiplier = models.FloatField(default=1.0, verbose_name='Multiplicateur de points')
    
    class Meta:
        verbose_name = 'Niveau de difficulté'
        verbose_name_plural = 'Niveaux de difficulté'
        ordering = ['level']
    
    def __str__(self):
        return f"{self.name} (Niveau {self.level})"


class Quiz(models.Model):
    """Quiz générés par IA"""
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Titre')
    slug = models.SlugField(max_length=200, unique=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes', verbose_name='Matière')
    difficulty = models.ForeignKey(DifficultyLevel, on_delete=models.CASCADE, related_name='quizzes', verbose_name='Difficulté')
    description = models.TextField(blank=True, verbose_name='Description')
    instructions = models.TextField(blank=True, verbose_name='Instructions')
    
    # Configuration du quiz
    time_limit = models.IntegerField(default=30, verbose_name='Durée limite (minutes)')
    max_attempts = models.IntegerField(default=3, verbose_name='Nombre maximum de tentatives')
    passing_score = models.IntegerField(default=70, verbose_name='Score de réussite (%)')
    
    # Points et récompenses
    points_available = models.IntegerField(default=100, verbose_name='Points disponibles')
    experience_points = models.IntegerField(default=50, verbose_name='Points d\'expérience')
    
    # IA et génération automatique
    is_ai_generated = models.BooleanField(default=True, verbose_name='Généré par IA')
    ai_prompt = models.TextField(blank=True, verbose_name='Prompt IA utilisé')
    ai_model_version = models.CharField(max_length=50, default='1.0', verbose_name='Version du modèle IA')
    
    # Métadonnées
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name='Statut')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_quizzes', verbose_name='Créé par')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    # Statistiques
    total_attempts = models.IntegerField(default=0, verbose_name='Total des tentatives')
    average_score = models.FloatField(default=0.0, verbose_name='Score moyen')
    
    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quiz'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Quiz.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('gamification:quiz_detail', kwargs={'slug': self.slug})
    
    def get_questions_count(self):
        return self.questions.count()
    
    def get_difficulty_display(self):
        return f"{self.difficulty.name} ({self.difficulty.level}/5)"


class Question(models.Model):
    """Questions du quiz"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Choix multiple'),
        ('true_false', 'Vrai/Faux'),
        ('fill_blank', 'Texte à trous'),
        ('essay', 'Question ouverte'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name='Quiz')
    question_text = models.TextField(verbose_name='Texte de la question')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice', verbose_name='Type de question')
    
    # Options pour choix multiple
    option_a = models.CharField(max_length=500, blank=True, verbose_name='Option A')
    option_b = models.CharField(max_length=500, blank=True, verbose_name='Option B')
    option_c = models.CharField(max_length=500, blank=True, verbose_name='Option C')
    option_d = models.CharField(max_length=500, blank=True, verbose_name='Option D')
    
    # Réponse correcte
    correct_answer = models.CharField(max_length=500, verbose_name='Réponse correcte')
    explanation = models.TextField(blank=True, verbose_name='Explication')
    
    # Points et difficulté
    points = models.IntegerField(default=10, verbose_name='Points')
    difficulty_score = models.FloatField(default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], verbose_name='Score de difficulté')
    
    # IA
    is_ai_generated = models.BooleanField(default=True, verbose_name='Généré par IA')
    ai_confidence = models.FloatField(default=0.8, verbose_name='Confiance IA')
    
    # Ordre et statut
    order = models.IntegerField(default=0, verbose_name='Ordre')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.question_text[:50]}..."
    
    def get_options(self):
        """Retourne les options sous forme de liste"""
        options = []
        if self.option_a:
            options.append(('A', self.option_a))
        if self.option_b:
            options.append(('B', self.option_b))
        if self.option_c:
            options.append(('C', self.option_c))
        if self.option_d:
            options.append(('D', self.option_d))
        return options


class QuizAttempt(models.Model):
    """Tentative de quiz par un étudiant"""
    STATUS_CHOICES = [
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('abandoned', 'Abandonné'),
        ('timeout', 'Temps écoulé'),
    ]
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts', verbose_name='Étudiant')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', verbose_name='Quiz')
    
    # Résultats
    score = models.FloatField(default=0.0, verbose_name='Score')
    percentage = models.FloatField(default=0.0, verbose_name='Pourcentage')
    points_earned = models.IntegerField(default=0, verbose_name='Points obtenus')
    experience_earned = models.IntegerField(default=0, verbose_name='Expérience obtenue')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Commencé à')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Terminé à')
    time_taken = models.IntegerField(default=0, verbose_name='Temps pris (secondes)')
    
    # Statut
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_progress', verbose_name='Statut')
    attempt_number = models.IntegerField(default=1, verbose_name='Numéro de tentative')
    
    # Réponses (stockées en JSON)
    answers = models.JSONField(default=dict, verbose_name='Réponses')
    
    class Meta:
        verbose_name = 'Tentative de quiz'
        verbose_name_plural = 'Tentatives de quiz'
        ordering = ['-started_at']
        unique_together = ['student', 'quiz', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} (Tentative {self.attempt_number})"
    
    def is_passed(self):
        return self.percentage >= self.quiz.passing_score
    
    def get_time_taken_display(self):
        minutes = self.time_taken // 60
        seconds = self.time_taken % 60
        return f"{minutes}m {seconds}s"


class Badge(models.Model):
    """Badges de gamification"""
    BADGE_TYPES = [
        ('achievement', 'Réussite'),
        ('streak', 'Série'),
        ('speed', 'Rapidité'),
        ('accuracy', 'Précision'),
        ('participation', 'Participation'),
        ('mastery', 'Maîtrise'),
        ('special', 'Spécial'),
    ]
    
    RARITY_LEVELS = [
        ('common', 'Commun'),
        ('uncommon', 'Peu commun'),
        ('rare', 'Rare'),
        ('epic', 'Épique'),
        ('legendary', 'Légendaire'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Nom')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(verbose_name='Description')
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, verbose_name='Type de badge')
    rarity = models.CharField(max_length=15, choices=RARITY_LEVELS, default='common', verbose_name='Rareté')
    
    # Visuel
    icon = models.CharField(max_length=50, default='bi-trophy', help_text='Classe d\'icône Bootstrap')
    color = models.CharField(max_length=7, default='#ffc107', help_text='Couleur hexadécimale')
    image = models.ImageField(upload_to='badges/', blank=True, null=True, verbose_name='Image du badge')
    
    # Conditions d'obtention
    condition_type = models.CharField(max_length=50, verbose_name='Type de condition')
    condition_value = models.IntegerField(verbose_name='Valeur de condition')
    condition_description = models.TextField(verbose_name='Description de la condition')
    
    # Récompenses
    points_reward = models.IntegerField(default=0, verbose_name='Points de récompense')
    experience_reward = models.IntegerField(default=0, verbose_name='Expérience de récompense')
    
    # Métadonnées
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'
        ordering = ['rarity', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('gamification:badge_detail', kwargs={'slug': self.slug})


class UserBadge(models.Model):
    """Badges obtenus par les utilisateurs"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges', verbose_name='Utilisateur')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users', verbose_name='Badge')
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='Obtenu le')
    context = models.JSONField(default=dict, verbose_name='Contexte d\'obtention')
    
    class Meta:
        verbose_name = 'Badge utilisateur'
        verbose_name_plural = 'Badges utilisateurs'
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class UserProfile(models.Model):
    """Profil de gamification de l'utilisateur"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gamification_profile', verbose_name='Utilisateur')
    
    # Points et expérience
    total_points = models.IntegerField(default=0, verbose_name='Points totaux')
    experience_points = models.IntegerField(default=0, verbose_name='Points d\'expérience')
    level = models.IntegerField(default=1, verbose_name='Niveau')
    
    # Statistiques
    quizzes_completed = models.IntegerField(default=0, verbose_name='Quiz complétés')
    quizzes_passed = models.IntegerField(default=0, verbose_name='Quiz réussis')
    total_attempts = models.IntegerField(default=0, verbose_name='Total des tentatives')
    average_score = models.FloatField(default=0.0, verbose_name='Score moyen')
    
    # Série et streaks
    current_streak = models.IntegerField(default=0, verbose_name='Série actuelle')
    longest_streak = models.IntegerField(default=0, verbose_name='Plus longue série')
    last_activity = models.DateTimeField(null=True, blank=True, verbose_name='Dernière activité')
    
    # Préférences
    favorite_subjects = models.ManyToManyField(Subject, blank=True, verbose_name='Matières préférées')
    preferred_difficulty = models.ForeignKey(DifficultyLevel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Difficulté préférée')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Profil de gamification'
        verbose_name_plural = 'Profils de gamification'
    
    def __str__(self):
        return f"Profil gamification de {self.user.username}"
    
    def calculate_level(self):
        """Calcule le niveau basé sur l'expérience"""
        # Formule: niveau = sqrt(exp / 100) + 1
        import math
        return int(math.sqrt(self.experience_points / 100)) + 1
    
    def get_level_progress(self):
        """Retourne le progrès vers le niveau suivant"""
        current_level_exp = (self.level - 1) ** 2 * 100
        next_level_exp = self.level ** 2 * 100
        progress = (self.experience_points - current_level_exp) / (next_level_exp - current_level_exp) * 100
        return min(100, max(0, progress))
    
    def get_rank(self):
        """Retourne le rang de l'utilisateur"""
        from django.db.models import F
        rank = UserProfile.objects.filter(
            experience_points__gt=self.experience_points
        ).count() + 1
        return rank


class Leaderboard(models.Model):
    """Classements"""
    LEADERBOARD_TYPES = [
        ('global', 'Global'),
        ('subject', 'Par matière'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('level', 'Par niveau'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Nom')
    leaderboard_type = models.CharField(max_length=15, choices=LEADERBOARD_TYPES, verbose_name='Type')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Matière')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Classement'
        verbose_name_plural = 'Classements'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_top_users(self, limit=10):
        """Retourne les meilleurs utilisateurs"""
        if self.leaderboard_type == 'subject' and self.subject:
            profiles = UserProfile.objects.filter(
                favorite_subjects=self.subject
            ).order_by('-experience_points')[:limit]
        else:
            profiles = UserProfile.objects.order_by('-experience_points')[:limit]
        
        return profiles


class Achievement(models.Model):
    """Réalisations spéciales"""
    name = models.CharField(max_length=100, verbose_name='Nom')
    description = models.TextField(verbose_name='Description')
    icon = models.CharField(max_length=50, default='bi-star', help_text='Classe d\'icône Bootstrap')
    points_reward = models.IntegerField(default=0, verbose_name='Points de récompense')
    experience_reward = models.IntegerField(default=0, verbose_name='Expérience de récompense')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Réalisation'
        verbose_name_plural = 'Réalisations'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Réalisations obtenues par les utilisateurs"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements', verbose_name='Utilisateur')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='users', verbose_name='Réalisation')
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name='Obtenu le')
    
    class Meta:
        verbose_name = 'Réalisation utilisateur'
        verbose_name_plural = 'Réalisations utilisateurs'
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"