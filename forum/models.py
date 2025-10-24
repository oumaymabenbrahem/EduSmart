from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """Catégorie de forum"""
    name = models.CharField(max_length=100, verbose_name='Nom')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(max_length=50, default='bi-chat-dots', help_text='Classe d\'icône Bootstrap')
    order = models.IntegerField(default=0, verbose_name='Ordre d\'affichage')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('forum:category_detail', kwargs={'slug': self.slug})


class Topic(models.Model):
    """Sujet de discussion"""
    STATUS_CHOICES = [
        ('open', 'Ouvert'),
        ('closed', 'Fermé'),
        ('pinned', 'Épinglé'),
    ]
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics', verbose_name='Catégorie')
    title = models.CharField(max_length=200, verbose_name='Titre')
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics', verbose_name='Auteur')
    content = models.TextField(verbose_name='Contenu')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', verbose_name='Statut')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    views = models.IntegerField(default=0, verbose_name='Vues')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    # Tags pour faciliter la recherche
    tags = models.CharField(max_length=200, blank=True, help_text='Séparez les tags par des virgules')
    
    class Meta:
        verbose_name = 'Sujet'
        verbose_name_plural = 'Sujets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Topic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('forum:topic_detail', kwargs={'slug': self.slug})
    
    def get_posts_count(self):
        """Retourne le nombre de posts actifs"""
        return self.posts.filter(is_active=True).count()
    
    def get_last_post(self):
        """Retourne le dernier post actif"""
        return self.posts.filter(is_active=True).order_by('-created_at').first()
    
    @property
    def first_post(self):
        """Retourne le premier post (contenu initial du topic)"""
        return self.posts.filter(is_active=True).order_by('created_at').first()
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])


class Post(models.Model):
    """Réponse/Post dans un sujet"""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts', verbose_name='Sujet')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts', verbose_name='Auteur')
    content = models.TextField(verbose_name='Contenu')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    is_solution = models.BooleanField(default=False, verbose_name='Solution acceptée')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    # Réaction/Likes
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)
    
    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Post de {self.author.username} sur {self.topic.title}"
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    def active_comments_count(self):
        """Retourne le nombre de commentaires actifs"""
        return self.comments.filter(is_active=True).count()


class Comment(models.Model):
    """Commentaire sur un post (réponse à une réponse)"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='Post')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', verbose_name='Auteur')
    content = models.TextField(verbose_name='Contenu')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.author.username}"


class Report(models.Model):
    """Signalement de contenu inapproprié"""
    CONTENT_TYPE_CHOICES = [
        ('topic', 'Sujet'),
        ('post', 'Post'),
        ('comment', 'Commentaire'),
    ]
    
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('offensive', 'Contenu offensant'),
        ('inappropriate', 'Contenu inapproprié'),
        ('other', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('reviewed', 'Examiné'),
        ('resolved', 'Résolu'),
        ('rejected', 'Rejeté'),
    ]
    
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, verbose_name='Type de contenu')
    content_id = models.IntegerField(verbose_name='ID du contenu')
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports', verbose_name='Signalé par')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, verbose_name='Raison')
    description = models.TextField(blank=True, verbose_name='Description')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='Statut')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports', verbose_name='Examiné par')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Résolu le')
    
    class Meta:
        verbose_name = 'Signalement'
        verbose_name_plural = 'Signalements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Signalement {self.content_type} #{self.content_id} par {self.reporter.username}"
    
    @classmethod
    def get_content_reports_count(cls, content_type, content_id):
        """Retourne le nombre de signalements en attente pour un contenu"""
        return cls.objects.filter(
            content_type=content_type,
            content_id=content_id,
            status='pending'
        ).count()
    
    @classmethod
    def get_user_reports_count(cls, user):
        """Retourne le nombre total de signalements reçus par un utilisateur"""
        from django.db.models import Q
        
        # Compter les signalements sur les topics de l'utilisateur
        topic_ids = Topic.objects.filter(author=user, is_active=True).values_list('id', flat=True)
        topic_reports = cls.objects.filter(content_type='topic', content_id__in=topic_ids, status='pending').count()
        
        # Compter les signalements sur les posts de l'utilisateur
        post_ids = Post.objects.filter(author=user, is_active=True).values_list('id', flat=True)
        post_reports = cls.objects.filter(content_type='post', content_id__in=post_ids, status='pending').count()
        
        # Compter les signalements sur les commentaires de l'utilisateur
        comment_ids = Comment.objects.filter(author=user, is_active=True).values_list('id', flat=True)
        comment_reports = cls.objects.filter(content_type='comment', content_id__in=comment_ids, status='pending').count()
        
        return topic_reports + post_reports + comment_reports
