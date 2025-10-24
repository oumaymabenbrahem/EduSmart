from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class Subject(models.Model):
    """Matières disponibles pour les cours"""
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
        return reverse('cours:subject_detail', kwargs={'slug': self.slug})


class Course(models.Model):
    """Cours disponibles"""
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]

    title = models.CharField(max_length=200, verbose_name='Titre')
    slug = models.SlugField(max_length=200, unique=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses', verbose_name='Matière')
    level = models.CharField(max_length=15, choices=LEVEL_CHOICES, default='beginner', verbose_name='Niveau')
    description = models.TextField(verbose_name='Description')
    content = models.TextField(verbose_name='Contenu du cours')
    objectives = models.TextField(blank=True, verbose_name='Objectifs d\'apprentissage')
    prerequisites = models.TextField(blank=True, verbose_name='Prérequis')

    # Métadonnées
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses', verbose_name='Instructeur')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name='Statut')
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    # Durée et difficulté
    duration_hours = models.IntegerField(default=1, verbose_name='Durée (heures)')
    difficulty_score = models.FloatField(default=0.5, verbose_name='Score de difficulté')

    # Médias
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True, verbose_name='Miniature')
    video_url = models.URLField(blank=True, verbose_name='URL de la vidéo')

    # Statistiques
    total_views = models.IntegerField(default=0, verbose_name='Nombre de vues')
    total_enrollments = models.IntegerField(default=0, verbose_name='Nombre d\'inscriptions')
    average_rating = models.FloatField(default=0.0, verbose_name='Note moyenne')

    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')

    class Meta:
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cours:course_detail', kwargs={'slug': self.slug})

    def get_level_display(self):
        return dict(self.LEVEL_CHOICES)[self.level]

    def increment_views(self):
        self.total_views += 1
        self.save(update_fields=['total_views'])


class CourseEnrollment(models.Model):
    """Inscription d'un étudiant à un cours"""
    STATUS_CHOICES = [
        ('enrolled', 'Inscrit'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('dropped', 'Abandonné'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_enrollments', verbose_name='Étudiant')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Cours')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='enrolled', verbose_name='Statut')
    progress_percentage = models.IntegerField(default=0, verbose_name='Progression (%)')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'inscription')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de completion')

    class Meta:
        verbose_name = 'Inscription au cours'
        verbose_name_plural = 'Inscriptions aux cours'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

    @property
    def is_completed(self):
        return self.status == 'completed'


class CourseReview(models.Model):
    """Avis sur un cours"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_reviews', verbose_name='Étudiant')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', verbose_name='Cours')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Note')
    comment = models.TextField(blank=True, verbose_name='Commentaire')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')

    class Meta:
        verbose_name = 'Avis sur cours'
        verbose_name_plural = 'Avis sur cours'
        unique_together = ['student', 'course']
        ordering = ['-created_at']

    def __str__(self):
        return f"Avis de {self.student.username} sur {self.course.title} ({self.rating}/5)"


class CourseModule(models.Model):
    """Modules d'un cours"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name='Cours')
    title = models.CharField(max_length=200, verbose_name='Titre')
    description = models.TextField(blank=True, verbose_name='Description')
    content_file = models.FileField(upload_to='courses/modules/', blank=True, null=True, verbose_name='Fichier du module')
    order = models.IntegerField(default=0, verbose_name='Ordre')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Module de cours'
        verbose_name_plural = 'Modules de cours'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseResource(models.Model):
    """Ressources d'un cours (documents, liens, etc.)"""
    RESOURCE_TYPES = [
        ('document', 'Document'),
        ('video', 'Vidéo'),
        ('link', 'Lien externe'),
        ('exercise', 'Exercice'),
        ('quiz', 'Quiz'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources', verbose_name='Cours')
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='resources', verbose_name='Module', null=True, blank=True)
    title = models.CharField(max_length=200, verbose_name='Titre')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='document', verbose_name='Type de ressource')
    description = models.TextField(blank=True, verbose_name='Description')
    file = models.FileField(upload_to='courses/resources/', blank=True, null=True, verbose_name='Fichier')
    url = models.URLField(blank=True, verbose_name='URL')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ressource de cours'
        verbose_name_plural = 'Ressources de cours'
        ordering = ['course', 'module', 'created_at']

    def __str__(self):
        return f"{self.course.title} - {self.title}"
