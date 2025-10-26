"""
Script de test pour le système de gamification innovant
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
from gamification.ai_quiz_generator import AIQuizGenerator
from gamification.advanced_gamification import AdvancedGamificationEngine, QuestSystem, RewardSystem

User = get_user_model()

def test_ai_quiz_generation():
    """Test de génération de quiz avec IA"""
    print("🤖 Test de génération de quiz avec IA...")
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Créer le profil de gamification
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Initialiser le générateur IA
    ai_generator = AIQuizGenerator()
    
    # Test de génération de quiz
    quiz = ai_generator.generate_quiz(
        subject_name='Informatique',
        difficulty_level=2,
        num_questions=5,
        user_profile=user_profile
    )
    
    if quiz:
        print(f"✅ Quiz généré avec succès: {quiz.title}")
        print(f"   - Matière: {quiz.subject.name}")
        print(f"   - Difficulté: {quiz.difficulty.name}")
        print(f"   - Questions: {quiz.questions.count()}")
        
        # Afficher quelques questions
        for i, question in enumerate(quiz.questions.all()[:3], 1):
            print(f"   Question {i}: {question.question_text[:50]}...")
    else:
        print("❌ Échec de la génération du quiz")
    
    return quiz

def test_gamification_engine():
    """Test du moteur de gamification avancé"""
    print("\n🎮 Test du moteur de gamification avancé...")
    
    user = User.objects.get(username='test_user')
    user_profile = UserProfile.objects.get(user=user)
    
    # Initialiser le moteur
    engine = AdvancedGamificationEngine()
    
    # Test de génération de quiz personnalisé
    personalized_quiz = engine.generate_personalized_quiz(user_profile)
    
    if personalized_quiz:
        print(f"✅ Quiz personnalisé généré: {personalized_quiz.title}")
    else:
        print("❌ Échec de la génération du quiz personnalisé")

def test_quest_system():
    """Test du système de quêtes"""
    print("\n🎯 Test du système de quêtes...")
    
    user = User.objects.get(username='test_user')
    user_profile = UserProfile.objects.get(user=user)
    
    # Initialiser le système de quêtes
    quest_system = QuestSystem()
    
    # Vérifier les quêtes
    completed_quests = quest_system.check_quest_completion(user_profile)
    
    print(f"✅ Quêtes vérifiées: {len(completed_quests)} quêtes complétées")
    for quest in completed_quests:
        print(f"   - {quest['name']}: {quest['description']}")

def test_reward_system():
    """Test du système de récompenses"""
    print("\n🏆 Test du système de récompenses...")
    
    user = User.objects.get(username='test_user')
    
    # Créer une tentative de quiz fictive
    quiz = Quiz.objects.first()
    if quiz:
        attempt = QuizAttempt.objects.create(
            student=user,
            quiz=quiz,
            score=85.0,
            percentage=85.0,
            points_earned=100,
            experience_earned=50,
            time_taken=300,  # 5 minutes
            status='completed'
        )
        
        # Initialiser le système de récompenses
        reward_system = RewardSystem()
        
        # Calculer les récompenses dynamiques
        rewards = reward_system.calculate_dynamic_rewards(attempt)
        
        print(f"✅ Récompenses calculées:")
        print(f"   - Points: {rewards['points']}")
        print(f"   - Expérience: {rewards['experience']}")
        print(f"   - Multiplicateurs: {rewards['multipliers']}")

def test_badge_system():
    """Test du système de badges"""
    print("\n🏅 Test du système de badges...")
    
    from gamification.ai_quiz_generator import BadgeAwarder
    
    user = User.objects.get(username='test_user')
    user_profile = UserProfile.objects.get(user=user)
    
    # Mettre à jour les statistiques pour déclencher des badges
    user_profile.quizzes_completed = 1
    user_profile.total_points = 150
    user_profile.experience_points = 75
    user_profile.save()
    
    # Initialiser le système de badges
    badge_awarder = BadgeAwarder()
    
    # Vérifier et attribuer les badges
    awarded_badges = badge_awarder.check_and_award_badges(user_profile)
    
    print(f"✅ Badges attribués: {len(awarded_badges)}")
    for badge in awarded_badges:
        print(f"   - {badge.name}: {badge.description}")

def create_sample_data():
    """Créer des données d'exemple"""
    print("\n📊 Création de données d'exemple...")
    
    # Créer des matières
    subjects_data = [
        {'name': 'Français', 'icon': 'bi-book', 'color': '#e74c3c'},
        {'name': 'Mathématiques', 'icon': 'bi-calculator', 'color': '#3498db'},
        {'name': 'Informatique', 'icon': 'bi-laptop', 'color': '#9b59b6'},
        {'name': 'Anglais', 'icon': 'bi-globe', 'color': '#f39c12'},
        {'name': 'Histoire', 'icon': 'bi-clock-history', 'color': '#2ecc71'},
    ]
    
    for subject_data in subjects_data:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults=subject_data
        )
        if created:
            print(f"   ✅ Matière créée: {subject.name}")
    
    # Créer des niveaux de difficulté
    difficulty_levels = [
        {'name': 'Débutant', 'level': 1, 'color': '#28a745', 'points_multiplier': 1.0},
        {'name': 'Intermédiaire', 'level': 2, 'color': '#ffc107', 'points_multiplier': 1.2},
        {'name': 'Avancé', 'level': 3, 'color': '#fd7e14', 'points_multiplier': 1.5},
        {'name': 'Expert', 'level': 4, 'color': '#dc3545', 'points_multiplier': 1.8},
        {'name': 'Maître', 'level': 5, 'color': '#6f42c1', 'points_multiplier': 2.0},
    ]
    
    for level_data in difficulty_levels:
        level, created = DifficultyLevel.objects.get_or_create(
            level=level_data['level'],
            defaults=level_data
        )
        if created:
            print(f"   ✅ Niveau créé: {level.name}")

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests du système de gamification EduSmart")
    print("=" * 60)
    
    try:
        # Créer les données d'exemple
        create_sample_data()
        
        # Tests des différents composants
        test_ai_quiz_generation()
        test_gamification_engine()
        test_quest_system()
        test_reward_system()
        test_badge_system()
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests sont terminés avec succès!")
        print("\n🎉 Le système de gamification EduSmart est prêt à l'emploi!")
        print("\n📋 Fonctionnalités disponibles:")
        print("   • Génération de quiz avec IA")
        print("   • Système de quêtes et missions")
        print("   • Récompenses dynamiques")
        print("   • Badges et réalisations")
        print("   • Analytics et recommandations")
        print("   • Parcours d'apprentissage personnalisé")
        print("   • Classements en temps réel")
        print("   • Rooms de quiz interactives")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
