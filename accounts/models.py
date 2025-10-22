from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from PIL import Image

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('student', 'Étudiant'),
        ('teacher', 'Enseignant'),
        ('admin', 'Administrateur'),
    ]
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student',
        verbose_name='Type d\'utilisateur'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name='Numéro de téléphone'
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date de naissance'
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name='Photo de profil'
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Biographie'
    )
    
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Adresse'
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ville'
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Pays'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Compte vérifié'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Dernière modification'
    )

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Redimensionner l'image de profil
        if self.profile_picture:
            img = Image.open(self.profile_picture.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_picture.path)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('accounts:profile', kwargs={'pk': self.pk})
