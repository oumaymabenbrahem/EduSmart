#!/usr/bin/env python
"""
Script d'initialisation des données de base pour la gamification
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from gamification.models import Subject, DifficultyLevel, Badge, Achievement
from gamification.ai_quiz_generator import BadgeAwarder


def create_subjects():
    """Créer les matières par défaut"""
    subjects_data = [
        {
            'name': 'Français',
            'description': 'Langue française, grammaire, littérature',
            'icon': 'bi-book',
            'color': '#e74c3c'
        },
        {
            'name': 'Mathématiques',
            'description': 'Algèbre, géométrie, calcul',
            'icon': 'bi-calculator',
            'color': '#3498db'
        },
        {
            'name': 'Informatique',
            'description': 'Programmation, algorithmes, bases de données',
            'icon': 'bi-laptop',
            'color': '#9b59b6'
        },
        {
            'name': 'Anglais',
            'description': 'Langue anglaise, vocabulaire, grammaire',
            'icon': 'bi-translate',
            'color': '#f39c12'
        },
        {
            'name': 'Histoire',
            'description': 'Histoire mondiale, chronologie, événements',
            'icon': 'bi-clock-history',
            'color': '#2ecc71'
        },
        {
            'name': 'Géographie',
            'description': 'Cartes, pays, capitales, climat',
            'icon': 'bi-globe',
            'color': '#1abc9c'
        },
        {
            'name': 'Sciences',
            'description': 'Physique, chimie, biologie',
            'icon': 'bi-flask',
            'color': '#e67e22'
        }
    ]
    
    created_count = 0
    for subject_data in subjects_data:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults=subject_data
        )
        if created:
            created_count += 1
            print(f"Matiere creee : {subject.name}")
    
    print(f"\n{created_count} nouvelles matieres creees")


def create_difficulty_levels():
    """Créer les niveaux de difficulté"""
    levels_data = [
        {
            'name': 'Débutant',
            'level': 1,
            'description': 'Niveau débutant - Questions faciles',
            'color': '#28a745',
            'points_multiplier': 1.0
        },
        {
            'name': 'Facile',
            'level': 2,
            'description': 'Niveau facile - Questions simples',
            'color': '#17a2b8',
            'points_multiplier': 1.2
        },
        {
            'name': 'Intermédiaire',
            'level': 3,
            'description': 'Niveau intermédiaire - Questions moyennes',
            'color': '#ffc107',
            'points_multiplier': 1.5
        },
        {
            'name': 'Difficile',
            'level': 4,
            'description': 'Niveau difficile - Questions complexes',
            'color': '#fd7e14',
            'points_multiplier': 2.0
        },
        {
            'name': 'Expert',
            'level': 5,
            'description': 'Niveau expert - Questions très difficiles',
            'color': '#dc3545',
            'points_multiplier': 3.0
        }
    ]
    
    created_count = 0
    for level_data in levels_data:
        level, created = DifficultyLevel.objects.get_or_create(
            level=level_data['level'],
            defaults=level_data
        )
        if created:
            created_count += 1
            print(f"Niveau cree : {level.name} (Niveau {level.level})")
    
    print(f"\n{created_count} nouveaux niveaux crees")


def create_achievements():
    """Créer les réalisations par défaut"""
    achievements_data = [
        {
            'name': 'Premier Quiz',
            'description': 'Complétez votre premier quiz',
            'icon': 'bi-star-fill',
            'points_reward': 50,
            'experience_reward': 25
        },
        {
            'name': 'Quiz Master',
            'description': 'Complétez 10 quiz',
            'icon': 'bi-trophy-fill',
            'points_reward': 200,
            'experience_reward': 100
        },
        {
            'name': 'Perfectionniste',
            'description': 'Obtenez 100% à un quiz',
            'icon': 'bi-check-circle-fill',
            'points_reward': 500,
            'experience_reward': 250
        },
        {
            'name': 'Série de 7',
            'description': 'Maintenez une série de 7 jours',
            'icon': 'bi-fire',
            'points_reward': 300,
            'experience_reward': 150
        },
        {
            'name': 'Polyvalent',
            'description': 'Complétez des quiz dans 5 matières différentes',
            'icon': 'bi-book-half',
            'points_reward': 400,
            'experience_reward': 200
        }
    ]
    
    created_count = 0
    for achievement_data in achievements_data:
        achievement, created = Achievement.objects.get_or_create(
            name=achievement_data['name'],
            defaults=achievement_data
        )
        if created:
            created_count += 1
            print(f"Realisation creee : {achievement.name}")
    
    print(f"\n{created_count} nouvelles realisations creees")


def initialize_badges():
    """Initialiser les badges avec le système d'attribution"""
    print("Initialisation des badges...")
    badge_awarder = BadgeAwarder()
    print(f"{len(badge_awarder.badges)} badges initialises")


def main():
    """Fonction principale"""
    print("Initialisation du systeme de gamification EduSmart")
    print("=" * 50)
    
    try:
        create_subjects()
        create_difficulty_levels()
        create_achievements()
        initialize_badges()
        
        print("\n" + "=" * 50)
        print("Initialisation terminee avec succes !")
        print("\nLe systeme de gamification est maintenant pret a etre utilise.")
        print("Vous pouvez :")
        print("- Acceder a /gamification/ pour voir l'interface")
        print("- Creer des quiz avec l'IA")
        print("- Gerer les badges et classements via l'admin")
        
    except Exception as e:
        print(f"\nErreur lors de l'initialisation : {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
