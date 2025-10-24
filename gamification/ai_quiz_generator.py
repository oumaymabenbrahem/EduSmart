try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

import json
import random
from django.conf import settings
from django.utils import timezone
from .models import Quiz, Question, Subject, DifficultyLevel, UserProfile, Badge, UserBadge


class AIQuizGenerator:
    """Générateur de quiz intelligent utilisant l'IA"""
    
    def __init__(self):
        # Configuration OpenAI (vous pouvez utiliser une clé API gratuite)
        self.api_key = getattr(settings, 'OPENAI_API_KEY', 'your-openai-api-key-here')
        self.model = "gpt-3.5-turbo"
        
    def generate_quiz(self, subject_name, difficulty_level, num_questions=10, user_profile=None):
        """Génère un quiz complet avec des questions"""
        try:
            # Récupérer ou créer la matière
            subject, created = Subject.objects.get_or_create(
                name=subject_name,
                defaults={
                    'description': f'Quiz sur {subject_name}',
                    'icon': 'bi-book',
                    'color': self._get_subject_color(subject_name)
                }
            )
            
            # Récupérer le niveau de difficulté
            difficulty = DifficultyLevel.objects.filter(level=difficulty_level).first()
            if not difficulty:
                difficulty = DifficultyLevel.objects.create(
                    name=f'Niveau {difficulty_level}',
                    level=difficulty_level,
                    description=f'Difficulté niveau {difficulty_level}',
                    points_multiplier=1.0 + (difficulty_level * 0.2)
                )
            
            # Générer le titre du quiz
            quiz_title = self._generate_quiz_title(subject_name, difficulty_level)
            
            # Créer le quiz
            quiz = Quiz.objects.create(
                title=quiz_title,
                subject=subject,
                difficulty=difficulty,
                description=f"Quiz généré par IA sur {subject_name} - Niveau {difficulty_level}",
                instructions="Répondez à toutes les questions dans le temps imparti. Bonne chance !",
                time_limit=self._calculate_time_limit(num_questions, difficulty_level),
                points_available=num_questions * 10,
                experience_points=num_questions * 5,
                is_ai_generated=True,
                ai_prompt=f"Générer un quiz sur {subject_name} niveau {difficulty_level}",
                created_by=user_profile.user if user_profile else None,
                status='published'
            )
            
            # Générer les questions
            questions_data = self._generate_questions(subject_name, difficulty_level, num_questions)
            
            for i, question_data in enumerate(questions_data):
                Question.objects.create(
                    quiz=quiz,
                    question_text=question_data['question'],
                    question_type=question_data['type'],
                    option_a=question_data.get('option_a', ''),
                    option_b=question_data.get('option_b', ''),
                    option_c=question_data.get('option_c', ''),
                    option_d=question_data.get('option_d', ''),
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data.get('explanation', ''),
                    points=question_data.get('points', 10),
                    difficulty_score=question_data.get('difficulty_score', 0.5),
                    is_ai_generated=True,
                    ai_confidence=question_data.get('confidence', 0.8),
                    order=i + 1
                )
            
            return quiz
            
        except Exception as e:
            print(f"Erreur lors de la génération du quiz: {e}")
            return None
    
    def _generate_quiz_title(self, subject, difficulty):
        """Génère un titre attractif pour le quiz"""
        titles = [
            f"Quiz {subject} - Niveau {difficulty}",
            f"Défi {subject} - Difficulté {difficulty}",
            f"Test de connaissances {subject}",
            f"Évaluation {subject} - Niveau {difficulty}",
            f"Quiz express {subject}"
        ]
        return random.choice(titles)
    
    def _get_subject_color(self, subject_name):
        """Retourne une couleur basée sur la matière"""
        colors = {
            'français': '#e74c3c',
            'mathématiques': '#3498db',
            'informatique': '#9b59b6',
            'anglais': '#f39c12',
            'histoire': '#2ecc71',
            'géographie': '#1abc9c',
            'sciences': '#e67e22',
            'physique': '#34495e',
            'chimie': '#8e44ad',
            'biologie': '#27ae60'
        }
        return colors.get(subject_name.lower(), '#007bff')
    
    def _calculate_time_limit(self, num_questions, difficulty):
        """Calcule le temps limite basé sur le nombre de questions et la difficulté"""
        base_time = num_questions * 2  # 2 minutes par question
        difficulty_multiplier = 1 + (difficulty * 0.2)
        return int(base_time * difficulty_multiplier)
    
    def _generate_questions(self, subject, difficulty, num_questions):
        """Génère les questions du quiz (version simplifiée sans OpenAI)"""
        # Pour cette démo, nous utilisons des questions prédéfinies
        # Dans un vrai projet, vous utiliseriez l'API OpenAI
        
        questions_templates = {
            'français': [
                {
                    'question': 'Quel est le genre du mot "table" ?',
                    'type': 'multiple_choice',
                    'option_a': 'Masculin',
                    'option_b': 'Féminin',
                    'option_c': 'Neutre',
                    'option_d': 'Variable',
                    'correct_answer': 'B',
                    'explanation': 'Le mot "table" est féminin.',
                    'points': 10,
                    'difficulty_score': 0.3,
                    'confidence': 0.9
                },
                {
                    'question': 'Quelle est la fonction du mot "très" dans la phrase "Il est très intelligent" ?',
                    'type': 'multiple_choice',
                    'option_a': 'Adjectif',
                    'option_b': 'Adverbe',
                    'option_c': 'Nom',
                    'option_d': 'Verbe',
                    'correct_answer': 'B',
                    'explanation': '"Très" est un adverbe qui modifie l\'adjectif "intelligent".',
                    'points': 15,
                    'difficulty_score': 0.6,
                    'confidence': 0.85
                }
            ],
            'mathématiques': [
                {
                    'question': 'Quel est le résultat de 15 + 27 ?',
                    'type': 'multiple_choice',
                    'option_a': '40',
                    'option_b': '42',
                    'option_c': '44',
                    'option_d': '46',
                    'correct_answer': 'B',
                    'explanation': '15 + 27 = 42',
                    'points': 10,
                    'difficulty_score': 0.2,
                    'confidence': 0.95
                },
                {
                    'question': 'Quelle est la dérivée de x² ?',
                    'type': 'multiple_choice',
                    'option_a': 'x',
                    'option_b': '2x',
                    'option_c': 'x²',
                    'option_d': '2x²',
                    'correct_answer': 'B',
                    'explanation': 'La dérivée de x² est 2x selon la règle de dérivation.',
                    'points': 20,
                    'difficulty_score': 0.8,
                    'confidence': 0.9
                }
            ],
            'informatique': [
                {
                    'question': 'Quel langage de programmation est utilisé pour le développement web frontend ?',
                    'type': 'multiple_choice',
                    'option_a': 'Python',
                    'option_b': 'JavaScript',
                    'option_c': 'Java',
                    'option_d': 'C++',
                    'correct_answer': 'B',
                    'explanation': 'JavaScript est principalement utilisé pour le développement web frontend.',
                    'points': 15,
                    'difficulty_score': 0.5,
                    'confidence': 0.85
                },
                {
                    'question': 'Qu\'est-ce qu\'une base de données relationnelle ?',
                    'type': 'multiple_choice',
                    'option_a': 'Une base de données sans structure',
                    'option_b': 'Une base de données organisée en tables liées',
                    'option_c': 'Une base de données uniquement textuelle',
                    'option_d': 'Une base de données sans index',
                    'correct_answer': 'B',
                    'explanation': 'Une base de données relationnelle organise les données en tables liées par des clés.',
                    'points': 20,
                    'difficulty_score': 0.7,
                    'confidence': 0.8
                }
            ],
            'anglais': [
                {
                    'question': 'Traduisez "Bonjour" en anglais.',
                    'type': 'multiple_choice',
                    'option_a': 'Goodbye',
                    'option_b': 'Hello',
                    'option_c': 'Good night',
                    'option_d': 'Good morning',
                    'correct_answer': 'B',
                    'explanation': '"Bonjour" se traduit par "Hello" en anglais.',
                    'points': 10,
                    'difficulty_score': 0.2,
                    'confidence': 0.95
                },
                {
                    'question': 'Quel est le participe passé de "to go" ?',
                    'type': 'multiple_choice',
                    'option_a': 'goed',
                    'option_b': 'gone',
                    'option_c': 'go',
                    'option_d': 'going',
                    'correct_answer': 'B',
                    'explanation': 'Le participe passé de "to go" est "gone".',
                    'points': 15,
                    'difficulty_score': 0.6,
                    'confidence': 0.9
                }
            ]
        }
        
        # Récupérer les questions pour la matière
        subject_questions = questions_templates.get(subject.lower(), questions_templates['français'])
        
        # Sélectionner le nombre de questions demandé
        selected_questions = random.sample(subject_questions, min(num_questions, len(subject_questions)))
        
        # Ajuster la difficulté
        for question in selected_questions:
            if difficulty >= 3:
                question['points'] = int(question['points'] * 1.5)
                question['difficulty_score'] = min(1.0, question['difficulty_score'] + 0.2)
        
        return selected_questions


class BadgeAwarder:
    """Système d'attribution automatique de badges"""
    
    def __init__(self):
        self.badges = self._initialize_badges()
    
    def _initialize_badges(self):
        """Initialise les badges par défaut"""
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
                'name': 'Maître',
                'description': 'Complétez 50 quiz',
                'badge_type': 'mastery',
                'rarity': 'rare',
                'icon': 'bi-trophy-fill',
                'color': '#ffc107',
                'condition_type': 'quizzes_completed',
                'condition_value': 50,
                'condition_description': 'Compléter 50 quiz',
                'points_reward': 1000,
                'experience_reward': 500
            },
            {
                'name': 'Série de 7',
                'description': 'Maintenez une série de 7 jours',
                'badge_type': 'streak',
                'rarity': 'uncommon',
                'icon': 'bi-fire',
                'color': '#dc3545',
                'condition_type': 'current_streak',
                'condition_value': 7,
                'condition_description': 'Maintenir une série de 7 jours',
                'points_reward': 300,
                'experience_reward': 150
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
            }
        ]
        
        badges = []
        for badge_data in badges_data:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            badges.append(badge)
        
        return badges
    
    def check_and_award_badges(self, user_profile):
        """Vérifie et attribue les badges à un utilisateur"""
        awarded_badges = []
        
        for badge in self.badges:
            # Vérifier si l'utilisateur a déjà ce badge
            if UserBadge.objects.filter(user=user_profile.user, badge=badge).exists():
                continue
            
            # Vérifier les conditions
            if self._check_badge_condition(user_profile, badge):
                UserBadge.objects.create(
                    user=user_profile.user,
                    badge=badge,
                    context={'earned_at': timezone.now().isoformat()}
                )
                
                # Ajouter les récompenses
                user_profile.total_points += badge.points_reward
                user_profile.experience_points += badge.experience_reward
                user_profile.save()
                
                awarded_badges.append(badge)
        
        return awarded_badges
    
    def _check_badge_condition(self, user_profile, badge):
        """Vérifie si l'utilisateur remplit les conditions pour un badge"""
        condition_type = badge.condition_type
        condition_value = badge.condition_value
        
        if condition_type == 'quizzes_completed':
            return user_profile.quizzes_completed >= condition_value
        elif condition_type == 'current_streak':
            return user_profile.current_streak >= condition_value
        elif condition_type == 'perfect_score':
            # Vérifier s'il y a un quiz avec 100%
            from .models import QuizAttempt
            return QuizAttempt.objects.filter(
                student=user_profile.user,
                percentage=100.0
            ).exists()
        
        return False


class LeaderboardManager:
    """Gestionnaire des classements"""
    
    def update_leaderboards(self):
        """Met à jour tous les classements"""
        leaderboards = Leaderboard.objects.filter(is_active=True)
        
        for leaderboard in leaderboards:
            self._update_leaderboard(leaderboard)
    
    def _update_leaderboard(self, leaderboard):
        """Met à jour un classement spécifique"""
        # Cette méthode pourrait être étendue pour des calculs plus complexes
        # Pour l'instant, elle utilise simplement les profils existants
        pass
    
    def get_global_leaderboard(self, limit=10):
        """Retourne le classement global"""
        return UserProfile.objects.order_by('-experience_points')[:limit]
    
    def get_subject_leaderboard(self, subject, limit=10):
        """Retourne le classement par matière"""
        return UserProfile.objects.filter(
            favorite_subjects=subject
        ).order_by('-experience_points')[:limit]
