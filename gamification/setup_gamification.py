"""
Script de configuration rapide pour le système de gamification EduSmart
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from gamification.models import *

User = get_user_model()

def create_basic_data():
    """Créer les données de base nécessaires"""
    print("📊 Création des données de base...")
    
    # Créer des matières
    subjects_data = [
        {'name': 'Français', 'icon': 'bi-book', 'color': '#e74c3c'},
        {'name': 'Mathématiques', 'icon': 'bi-calculator', 'color': '#3498db'},
        {'name': 'Informatique', 'icon': 'bi-laptop', 'color': '#9b59b6'},
        {'name': 'Anglais', 'icon': 'bi-globe', 'color': '#f39c12'},
        {'name': 'Histoire', 'icon': 'bi-clock-history', 'color': '#2ecc71'},
        {'name': 'Sciences', 'icon': 'bi-flask', 'color': '#e67e22'},
    ]
    
    for subject_data in subjects_data:
        try:
            subject = Subject.objects.get(name=subject_data['name'])
            print(f"   ✅ Matière existante: {subject.name}")
        except Subject.DoesNotExist:
            subject = Subject.objects.create(**subject_data)
            print(f"   ✅ Matière créée: {subject.name}")
    
    # Créer des niveaux de difficulté
    difficulty_levels = [
        {'name': 'Très Facile', 'level': 1, 'color': '#28a745', 'points_multiplier': 0.8},
        {'name': 'Facile', 'level': 2, 'color': '#6f42c1', 'points_multiplier': 1.0},
        {'name': 'Moyen', 'level': 3, 'color': '#ffc107', 'points_multiplier': 1.2},
        {'name': 'Difficile', 'level': 4, 'color': '#fd7e14', 'points_multiplier': 1.5},
        {'name': 'Très Difficile', 'level': 5, 'color': '#dc3545', 'points_multiplier': 2.0},
    ]
    
    for level_data in difficulty_levels:
        try:
            level = DifficultyLevel.objects.get(level=level_data['level'])
            print(f"   ✅ Niveau existant: {level.name}")
        except DifficultyLevel.DoesNotExist:
            level = DifficultyLevel.objects.create(**level_data)
            print(f"   ✅ Niveau créé: {level.name}")

def create_sample_badges():
    """Créer des badges d'exemple"""
    print("🏅 Création des badges...")
    
    badges_data = [
        {
            'name': 'Premier Pas',
            'description': 'Complétez votre premier quiz',
            'badge_type': 'achievement',
            'rarity': 'common',
            'icon': 'bi-star-fill',
            'color': '#28a745',
            'condition_type': 'quizzes_completed',
            'condition_value': 1,
            'condition_description': 'Compléter 1 quiz',
            'points_reward': 50,
            'experience_reward': 25
        },
        {
            'name': 'Érudit',
            'description': 'Complétez 10 quiz',
            'badge_type': 'achievement',
            'rarity': 'uncommon',
            'icon': 'bi-book-fill',
            'color': '#007bff',
            'condition_type': 'quizzes_completed',
            'condition_value': 10,
            'condition_description': 'Compléter 10 quiz',
            'points_reward': 200,
            'experience_reward': 100
        },
        {
            'name': 'Perfectionniste',
            'description': 'Obtenez 100% à un quiz',
            'badge_type': 'accuracy',
            'rarity': 'rare',
            'icon': 'bi-check-circle-fill',
            'color': '#28a745',
            'condition_type': 'perfect_score',
            'condition_value': 1,
            'condition_description': 'Obtenir 100% à un quiz',
            'points_reward': 500,
            'experience_reward': 250
        },
        {
            'name': 'Série de Feu',
            'description': 'Maintenez une série de 7 jours',
            'badge_type': 'streak',
            'rarity': 'epic',
            'icon': 'bi-fire',
            'color': '#dc3545',
            'condition_type': 'current_streak',
            'condition_value': 7,
            'condition_description': 'Maintenir une série de 7 jours',
            'points_reward': 300,
            'experience_reward': 150
        },
        {
            'name': 'Légende',
            'description': 'Complétez 100 quiz',
            'badge_type': 'mastery',
            'rarity': 'legendary',
            'icon': 'bi-trophy-fill',
            'color': '#ffd700',
            'condition_type': 'quizzes_completed',
            'condition_value': 100,
            'condition_description': 'Compléter 100 quiz',
            'points_reward': 2000,
            'experience_reward': 1000
        }
    ]
    
    for badge_data in badges_data:
        try:
            badge = Badge.objects.get(name=badge_data['name'])
            print(f"   ✅ Badge existant: {badge.name}")
        except Badge.DoesNotExist:
            badge = Badge.objects.create(**badge_data)
            print(f"   ✅ Badge créé: {badge.name}")

def create_sample_quiz():
    """Créer un quiz d'exemple"""
    print("📝 Création d'un quiz d'exemple...")
    
    try:
        # Récupérer la matière informatique
        informatique = Subject.objects.get(name='Informatique')
        facile = DifficultyLevel.objects.get(level=2)
        
        # Créer un utilisateur admin si nécessaire
        admin_user, created = User.objects.get_or_create(
            username='system_admin',
            defaults={
                'email': 'admin@edusmart.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'is_staff': True
            }
        )
        
        # Créer le quiz
        quiz, created = Quiz.objects.get_or_create(
            title='Quiz de Démarrage - Informatique',
            defaults={
                'subject': informatique,
                'difficulty': facile,
                'description': 'Un quiz simple pour commencer votre aventure !',
                'instructions': 'Répondez à toutes les questions. Bonne chance !',
                'time_limit': 10,
                'points_available': 100,
                'experience_points': 50,
                'is_ai_generated': False,
                'status': 'published',
                'created_by': admin_user
            }
        )
        
        if created:
            print(f"   ✅ Quiz créé: {quiz.title}")
            
            # Ajouter quelques questions
            questions_data = [
                {
                    'question_text': 'Quel est le langage de programmation le plus populaire en 2024 ?',
                    'question_type': 'multiple_choice',
                    'option_a': 'Java',
                    'option_b': 'Python',
                    'option_c': 'JavaScript',
                    'option_d': 'C++',
                    'correct_answer': 'B',
                    'explanation': 'Python est actuellement le langage le plus populaire grâce à sa simplicité et sa polyvalence.',
                    'points': 25,
                    'order': 1
                },
                {
                    'question_text': 'Que signifie HTML ?',
                    'question_type': 'multiple_choice',
                    'option_a': 'Hypertext Markup Language',
                    'option_b': 'High Tech Modern Language',
                    'option_c': 'Home Tool Markup Language',
                    'option_d': 'Hyperlink and Text Markup Language',
                    'correct_answer': 'A',
                    'explanation': 'HTML signifie HyperText Markup Language, le langage de balisage pour les pages web.',
                    'points': 25,
                    'order': 2
                },
                {
                    'question_text': 'Qu\'est-ce qu\'un algorithme ?',
                    'question_type': 'multiple_choice',
                    'option_a': 'Un type de données',
                    'option_b': 'Une suite d\'instructions pour résoudre un problème',
                    'option_c': 'Un langage de programmation',
                    'option_d': 'Un système d\'exploitation',
                    'correct_answer': 'B',
                    'explanation': 'Un algorithme est une suite d\'instructions logiques pour résoudre un problème.',
                    'points': 25,
                    'order': 3
                },
                {
                    'question_text': 'Quel est le rôle d\'une base de données ?',
                    'question_type': 'multiple_choice',
                    'option_a': 'Stocker et organiser des données',
                    'option_b': 'Créer des sites web',
                    'option_c': 'Programmer des applications',
                    'option_d': 'Gérer les réseaux',
                    'correct_answer': 'A',
                    'explanation': 'Une base de données sert à stocker, organiser et gérer des données de manière structurée.',
                    'points': 25,
                    'order': 4
                }
            ]
            
            for question_data in questions_data:
                Question.objects.create(quiz=quiz, **question_data)
            
            print(f"   ✅ {len(questions_data)} questions ajoutées")
        else:
            print(f"   ✅ Quiz existant: {quiz.title}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la création du quiz: {e}")

def main():
    """Fonction principale de configuration"""
    print("🚀 Configuration du système de gamification EduSmart")
    print("=" * 60)
    
    try:
        create_basic_data()
        create_sample_badges()
        create_sample_quiz()
        
        print("\n" + "=" * 60)
        print("✅ Configuration terminée avec succès!")
        print("\n🎯 Prochaines étapes:")
        print("   1. Démarrez le serveur Django: python manage.py runserver")
        print("   2. Accédez au dashboard: http://127.0.0.1:8000/gamification/dashboard/")
        print("   3. Créez un compte utilisateur et commencez à jouer!")
        print("\n🎮 Fonctionnalités disponibles:")
        print("   • Dashboard interactif")
        print("   • Génération de quiz IA")
        print("   • Système de badges")
        print("   • Classements en temps réel")
        print("   • Parcours personnalisés")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
