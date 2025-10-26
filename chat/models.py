from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q


class ChatRoom(models.Model):
    """
    Représente une conversation entre deux utilisateurs
    """
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='chat_rooms_as_participant1'
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='chat_rooms_as_participant2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']
        # Assurer qu'il n'y a qu'une seule conversation entre deux utilisateurs
        constraints = [
            models.UniqueConstraint(
                fields=['participant1', 'participant2'],
                name='unique_chat_room'
            )
        ]
    
    def __str__(self):
        return f"Chat entre {self.participant1.username} et {self.participant2.username}"
    
    def get_other_participant(self, user):
        """Retourne l'autre participant de la conversation"""
        return self.participant2 if self.participant1 == user else self.participant1
    
    def get_last_message(self):
        """Retourne le dernier message de la conversation"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """Retourne le nombre de messages non lus pour l'utilisateur"""
        return self.messages.filter(
            sender__ne=user,
            is_read=False
        ).count()
    
    @classmethod
    def get_or_create_room(cls, user1, user2):
        """
        Crée ou récupère une conversation entre deux utilisateurs
        Gère l'ordre des participants pour éviter les doublons
        """
        # S'assurer que participant1.id < participant2.id
        if user1.id > user2.id:
            user1, user2 = user2, user1
        
        room, created = cls.objects.get_or_create(
            participant1=user1,
            participant2=user2
        )
        return room, created


class Message(models.Model):
    """
    Représente un message dans une conversation
    """
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat_room', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message de {self.sender.username} à {self.created_at}"
    
    def mark_as_read(self):
        """Marque le message comme lu"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def soft_delete(self):
        """Suppression douce du message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class MessageAttachment(models.Model):
    """
    Représente une pièce jointe à un message
    """
    FILE_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('other', 'Autre'),
    ]
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.IntegerField(help_text="Taille en octets")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Fichier: {self.file_name}"
    
    def get_file_size_display(self):
        """Retourne la taille du fichier en format lisible"""
        size = self.file_size
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} To"


class UserStatus(models.Model):
    """
    Statut en ligne de l'utilisateur
    """
    STATUS_CHOICES = [
        ('online', 'En ligne'),
        ('away', 'Absent'),
        ('busy', 'Occupé'),
        ('offline', 'Hors ligne'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_status'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='offline'
    )
    last_activity = models.DateTimeField(default=timezone.now)
    custom_message = models.CharField(
        max_length=100,
        blank=True,
        help_text="Message de statut personnalisé"
    )
    
    class Meta:
        verbose_name = 'Statut utilisateur'
        verbose_name_plural = 'Statuts utilisateurs'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"
    
    def is_online(self):
        """Vérifie si l'utilisateur est en ligne (actif dans les 5 dernières minutes)"""
        if self.status == 'offline':
            return False
        time_diff = timezone.now() - self.last_activity
        return time_diff.total_seconds() < 300  # 5 minutes
    
    def update_activity(self):
        """Met à jour le timestamp de la dernière activité"""
        self.last_activity = timezone.now()
        if self.status == 'offline':
            self.status = 'online'
        self.save(update_fields=['last_activity', 'status'])
