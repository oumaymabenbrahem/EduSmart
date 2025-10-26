try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

import json
import random
import os
from django.conf import settings
from django.utils import timezone
from .models import Quiz, Question, Subject, DifficultyLevel, UserProfile, Badge, UserBadge
from .settings import OPENAI_API_KEY


class AIQuizGenerator:
    """Générateur de quiz intelligent utilisant l'IA"""
    
    def __init__(self):
        # Configuration OpenAI avec gestion sécurisée de la clé API
        self.api_key = OPENAI_API_KEY or os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4o-mini"
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Erreur d'initialisation OpenAI: {e}")
                self.client = None
        
    def generate_quiz(self, subject_name, difficulty_level, num_questions=10, user_profile=None):
        """Génère un quiz complet avec des questions"""
        try:
            # Récupérer ou créer la matière avec gestion du slug
            try:
                subject = Subject.objects.get(name=subject_name)
            except Subject.DoesNotExist:
                subject = Subject.objects.create(
                    name=subject_name,
                    description=f'Quiz sur {subject_name}',
                    icon='bi-book',
                    color=self._get_subject_color(subject_name)
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
            
            # Générer les questions avec IA si disponible, sinon utiliser les templates
            if self.client and OPENAI_AVAILABLE:
                questions_data = self._generate_ai_questions(subject_name, difficulty_level, num_questions)
            else:
                questions_data = self._generate_template_questions(subject_name, difficulty_level, num_questions)
            
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
    
    def _generate_ai_questions(self, subject, difficulty, num_questions):
        """Génère des questions en utilisant l'API OpenAI"""
        try:
            prompt = f"""
Créez {num_questions} questions de quiz sur le sujet "{subject}" avec un niveau de difficulté {difficulty}/5.

Format de réponse JSON :
{{
  "questions": [
    {{
      "question": "Texte de la question",
      "type": "multiple_choice",
      "option_a": "Option A",
      "option_b": "Option B",
      "option_c": "Option C",
      "option_d": "Option D",
      "correct_answer": "A",
      "explanation": "Explication de la réponse",
      "points": 10,
      "difficulty_score": 0.5,
      "confidence": 0.9
    }}
  ]
}}

Assurez-vous que :
- Les questions sont pertinentes au sujet
- Le niveau de difficulté correspond à {difficulty}/5
- Les explications sont claires et éducatives
- Une seule réponse est correcte par question
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en création de quiz éducatifs. Créez des questions de qualité avec des explications claires."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parser la réponse JSON
            ai_response = response.choices[0].message.content
            questions_json = json.loads(ai_response)
            
            return questions_json.get('questions', [])
            
        except Exception as e:
            print(f"Erreur lors de la génération IA: {e}")
            # Fallback vers les templates
            return self._generate_template_questions(subject, difficulty, num_questions)
    
    def _generate_template_questions(self, subject, difficulty, num_questions):
        """Génère les questions du quiz avec beaucoup plus de contenu réel"""

        questions_templates = {
            'français': [
                # Grammaire
                {'question': 'Quel est le genre du mot "table" ?', 'type': 'multiple_choice', 'option_a': 'Masculin', 'option_b': 'Féminin', 'option_c': 'Neutre', 'option_d': 'Variable', 'correct_answer': 'B', 'explanation': 'Le mot "table" est féminin.', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.9},
                {'question': 'Quelle est la fonction du mot "très" dans "Il est très intelligent" ?', 'type': 'multiple_choice', 'option_a': 'Adjectif', 'option_b': 'Adverbe', 'option_c': 'Nom', 'option_d': 'Verbe', 'correct_answer': 'B', 'explanation': '"Très" est un adverbe qui modifie l\'adjectif "intelligent".', 'points': 15, 'difficulty_score': 0.6, 'confidence': 0.85},
                {'question': 'Quel est le pluriel de "cheval" ?', 'type': 'multiple_choice', 'option_a': 'chevales', 'option_b': 'chevaux', 'option_c': 'chevals', 'option_d': 'chevals', 'correct_answer': 'B', 'explanation': 'Le pluriel de "cheval" est "chevaux".', 'points': 10, 'difficulty_score': 0.4, 'confidence': 0.95},
                {'question': 'Quel temps verbal est utilisé dans "Je suis allé au marché" ?', 'type': 'multiple_choice', 'option_a': 'Présent', 'option_b': 'Imparfait', 'option_c': 'Passé composé', 'option_d': 'Futur', 'correct_answer': 'C', 'explanation': '"Je suis allé" est au passé composé.', 'points': 15, 'difficulty_score': 0.5, 'confidence': 0.9},
                {'question': 'Quel est le contraire de "beau" ?', 'type': 'multiple_choice', 'option_a': 'Joli', 'option_b': 'Laid', 'option_c': 'Magnifique', 'option_d': 'Splendide', 'correct_answer': 'B', 'explanation': 'Le contraire de "beau" est "laid".', 'points': 10, 'difficulty_score': 0.2, 'confidence': 0.95},
                {'question': 'Quel est le sujet de la phrase "Les enfants jouent dans le parc" ?', 'type': 'multiple_choice', 'option_a': 'jouent', 'option_b': 'parc', 'option_c': 'Les enfants', 'option_d': 'dans', 'correct_answer': 'C', 'explanation': '"Les enfants" est le sujet de la phrase.', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.92},
                {'question': 'Quel est le complément d\'objet direct dans "Je mange une pomme" ?', 'type': 'multiple_choice', 'option_a': 'Je', 'option_b': 'mange', 'option_c': 'une pomme', 'option_d': 'une', 'correct_answer': 'C', 'explanation': '"une pomme" est le complément d\'objet direct.', 'points': 15, 'difficulty_score': 0.6, 'confidence': 0.88},
                {'question': 'Quel est le participe passé de "faire" ?', 'type': 'multiple_choice', 'option_a': 'faisait', 'option_b': 'fait', 'option_c': 'faisant', 'option_d': 'fasse', 'correct_answer': 'B', 'explanation': 'Le participe passé de "faire" est "fait".', 'points': 10, 'difficulty_score': 0.4, 'confidence': 0.93},
                {'question': 'Quel est le synonyme de "rapide" ?', 'type': 'multiple_choice', 'option_a': 'Lent', 'option_b': 'Véloce', 'option_c': 'Lourd', 'option_d': 'Faible', 'correct_answer': 'B', 'explanation': '"Véloce" est un synonyme de "rapide".', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.9},
                {'question': 'Quel est le mode du verbe dans "Que tu viennes" ?', 'type': 'multiple_choice', 'option_a': 'Indicatif', 'option_b': 'Conditionnel', 'option_c': 'Subjonctif', 'option_d': 'Impératif', 'correct_answer': 'C', 'explanation': '"Que tu viennes" est au subjonctif.', 'points': 20, 'difficulty_score': 0.8, 'confidence': 0.85},
            ],
            'mathématiques': [
                # Arithmétique et Algèbre
                {'question': 'Quel est le résultat de 15 + 27 ?', 'type': 'multiple_choice', 'option_a': '40', 'option_b': '42', 'option_c': '44', 'option_d': '46', 'correct_answer': 'B', 'explanation': '15 + 27 = 42', 'points': 10, 'difficulty_score': 0.2, 'confidence': 0.95},
                {'question': 'Quelle est la dérivée de x² ?', 'type': 'multiple_choice', 'option_a': 'x', 'option_b': '2x', 'option_c': 'x²', 'option_d': '2x²', 'correct_answer': 'B', 'explanation': 'La dérivée de x² est 2x.', 'points': 20, 'difficulty_score': 0.8, 'confidence': 0.9},
                {'question': 'Quel est le résultat de 48 ÷ 6 ?', 'type': 'multiple_choice', 'option_a': '6', 'option_b': '7', 'option_c': '8', 'option_d': '9', 'correct_answer': 'C', 'explanation': '48 ÷ 6 = 8', 'points': 10, 'difficulty_score': 0.2, 'confidence': 0.95},
                {'question': 'Quel est le résultat de 12 × 5 ?', 'type': 'multiple_choice', 'option_a': '50', 'option_b': '55', 'option_c': '60', 'option_d': '65', 'correct_answer': 'C', 'explanation': '12 × 5 = 60', 'points': 10, 'difficulty_score': 0.2, 'confidence': 0.95},
                {'question': 'Quel est le résultat de 2³ ?', 'type': 'multiple_choice', 'option_a': '6', 'option_b': '8', 'option_c': '9', 'option_d': '12', 'correct_answer': 'B', 'explanation': '2³ = 2 × 2 × 2 = 8', 'points': 15, 'difficulty_score': 0.4, 'confidence': 0.92},
                {'question': 'Quel est le résultat de √16 ?', 'type': 'multiple_choice', 'option_a': '2', 'option_b': '3', 'option_c': '4', 'option_d': '5', 'correct_answer': 'C', 'explanation': '√16 = 4', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.95},
                {'question': 'Quel est le résultat de 25% de 80 ?', 'type': 'multiple_choice', 'option_a': '15', 'option_b': '20', 'option_c': '25', 'option_d': '30', 'correct_answer': 'B', 'explanation': '25% de 80 = 0.25 × 80 = 20', 'points': 15, 'difficulty_score': 0.5, 'confidence': 0.9},
                {'question': 'Quel est le résultat de 3x + 5 = 20 ?', 'type': 'multiple_choice', 'option_a': 'x = 3', 'option_b': 'x = 5', 'option_c': 'x = 7', 'option_d': 'x = 10', 'correct_answer': 'B', 'explanation': '3x + 5 = 20 → 3x = 15 → x = 5', 'points': 20, 'difficulty_score': 0.6, 'confidence': 0.88},
                {'question': 'Quel est le résultat de (2 + 3) × 4 ?', 'type': 'multiple_choice', 'option_a': '14', 'option_b': '18', 'option_c': '20', 'option_d': '24', 'correct_answer': 'C', 'explanation': '(2 + 3) × 4 = 5 × 4 = 20', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.93},
                {'question': 'Quel est le résultat de 100 - 45 + 20 ?', 'type': 'multiple_choice', 'option_a': '65', 'option_b': '70', 'option_c': '75', 'option_d': '80', 'correct_answer': 'C', 'explanation': '100 - 45 + 20 = 55 + 20 = 75', 'points': 10, 'difficulty_score': 0.2, 'confidence': 0.95},
            ],
            'informatique': [
                {'question': 'Quel langage est utilisé pour le développement web frontend ?', 'type': 'multiple_choice', 'option_a': 'Python', 'option_b': 'JavaScript', 'option_c': 'Java', 'option_d': 'C++', 'correct_answer': 'B', 'explanation': 'JavaScript est principalement utilisé pour le développement web frontend.', 'points': 15, 'difficulty_score': 0.5, 'confidence': 0.85},
                {'question': 'Qu\'est-ce qu\'une base de données relationnelle ?', 'type': 'multiple_choice', 'option_a': 'Une base sans structure', 'option_b': 'Une base organisée en tables liées', 'option_c': 'Une base uniquement textuelle', 'option_d': 'Une base sans index', 'correct_answer': 'B', 'explanation': 'Une base de données relationnelle organise les données en tables liées par des clés.', 'points': 20, 'difficulty_score': 0.7, 'confidence': 0.8},
                {'question': 'Quel est le langage de balisage pour les pages web ?', 'type': 'multiple_choice', 'option_a': 'CSS', 'option_b': 'HTML', 'option_c': 'JavaScript', 'option_d': 'Python', 'correct_answer': 'B', 'explanation': 'HTML est le langage de balisage pour les pages web.', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.95},
                {'question': 'Quel est le langage de style pour les pages web ?', 'type': 'multiple_choice', 'option_a': 'HTML', 'option_b': 'JavaScript', 'option_c': 'CSS', 'option_d': 'Python', 'correct_answer': 'C', 'explanation': 'CSS est utilisé pour styliser les pages web.', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.95},
                {'question': 'Qu\'est-ce qu\'un algorithme ?', 'type': 'multiple_choice', 'option_a': 'Un type de données', 'option_b': 'Une suite d\'instructions pour résoudre un problème', 'option_c': 'Un langage de programmation', 'option_d': 'Un système d\'exploitation', 'correct_answer': 'B', 'explanation': 'Un algorithme est une suite d\'instructions pour résoudre un problème.', 'points': 15, 'difficulty_score': 0.6, 'confidence': 0.9},
                {'question': 'Quel est le langage de programmation le plus utilisé ?', 'type': 'multiple_choice', 'option_a': 'Java', 'option_b': 'Python', 'option_c': 'C++', 'option_d': 'JavaScript', 'correct_answer': 'B', 'explanation': 'Python est actuellement le langage de programmation le plus populaire.', 'points': 15, 'difficulty_score': 0.5, 'confidence': 0.85},
                {'question': 'Qu\'est-ce qu\'une variable en programmation ?', 'type': 'multiple_choice', 'option_a': 'Un type de boucle', 'option_b': 'Un conteneur pour stocker une valeur', 'option_c': 'Une fonction', 'option_d': 'Un commentaire', 'correct_answer': 'B', 'explanation': 'Une variable est un conteneur pour stocker une valeur en programmation.', 'points': 10, 'difficulty_score': 0.4, 'confidence': 0.92},
                {'question': 'Qu\'est-ce qu\'une boucle for ?', 'type': 'multiple_choice', 'option_a': 'Une condition', 'option_b': 'Une structure pour répéter du code', 'option_c': 'Une fonction', 'option_d': 'Un tableau', 'correct_answer': 'B', 'explanation': 'Une boucle for est une structure pour répéter du code un nombre de fois.', 'points': 15, 'difficulty_score': 0.5, 'confidence': 0.9},
                {'question': 'Qu\'est-ce qu\'une fonction en programmation ?', 'type': 'multiple_choice', 'option_a': 'Une variable', 'option_b': 'Un bloc de code réutilisable', 'option_c': 'Une boucle', 'option_d': 'Un commentaire', 'correct_answer': 'B', 'explanation': 'Une fonction est un bloc de code réutilisable en programmation.', 'points': 15, 'difficulty_score': 0.6, 'confidence': 0.88},
                {'question': 'Qu\'est-ce qu\'un tableau en programmation ?', 'type': 'multiple_choice', 'option_a': 'Une variable', 'option_b': 'Une fonction', 'option_c': 'Une collection d\'éléments', 'option_d': 'Une boucle', 'correct_answer': 'C', 'explanation': 'Un tableau est une collection d\'éléments en programmation.', 'points': 10, 'difficulty_score': 0.4, 'confidence': 0.92},
            ],
            'anglais': [
                {'question': 'Traduisez "Bonjour" en anglais.', 'type': 'multiple_choice', 'option_a': 'Goodbye', 'option_b': 'Hello', 'option_c': 'Good night', 'option_d': 'Good morning', 'correct_answer': 'B', 'explanation': '"Bonjour" se traduit par "Hello" en anglais.', 'points': 10, 'difficulty_score': 0.2, 'confidence': 0.95},
                {'question': 'Quel est le participe passé de "to go" ?', 'type': 'multiple_choice', 'option_a': 'goed', 'option_b': 'gone', 'option_c': 'go', 'option_d': 'going', 'correct_answer': 'B', 'explanation': 'Le participe passé de "to go" est "gone".', 'points': 15, 'difficulty_score': 0.6, 'confidence': 0.9},
                {'question': 'Quel est le présent simple de "to be" à la 3ème personne du singulier ?', 'type': 'multiple_choice', 'option_a': 'am', 'option_b': 'are', 'option_c': 'is', 'option_d': 'be', 'correct_answer': 'C', 'explanation': 'Le présent simple de "to be" à la 3ème personne du singulier est "is".', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.95},
                {'question': 'Traduisez "Je suis heureux" en anglais.', 'type': 'multiple_choice', 'option_a': 'I am happy', 'option_b': 'I is happy', 'option_c': 'I are happy', 'option_d': 'I be happy', 'correct_answer': 'A', 'explanation': '"Je suis heureux" se traduit par "I am happy".', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.95},
                {'question': 'Quel est le pluriel de "child" ?', 'type': 'multiple_choice', 'option_a': 'childs', 'option_b': 'childes', 'option_c': 'children', 'option_d': 'childrens', 'correct_answer': 'C', 'explanation': 'Le pluriel de "child" est "children".', 'points': 10, 'difficulty_score': 0.4, 'confidence': 0.93},
                {'question': 'Quel est le passé simple de "to eat" ?', 'type': 'multiple_choice', 'option_a': 'eated', 'option_b': 'ate', 'option_c': 'eating', 'option_d': 'eat', 'correct_answer': 'B', 'explanation': 'Le passé simple de "to eat" est "ate".', 'points': 15, 'difficulty_score': 0.5, 'confidence': 0.92},
                {'question': 'Traduisez "Quelle heure est-il ?" en anglais.', 'type': 'multiple_choice', 'option_a': 'What time is it?', 'option_b': 'What is the time?', 'option_c': 'What time it is?', 'option_d': 'What time are it?', 'correct_answer': 'A', 'explanation': '"Quelle heure est-il ?" se traduit par "What time is it?"', 'points': 15, 'difficulty_score': 0.5, 'confidence': 0.9},
                {'question': 'Quel est le comparatif de "big" ?', 'type': 'multiple_choice', 'option_a': 'biger', 'option_b': 'bigger', 'option_c': 'more big', 'option_d': 'bigest', 'correct_answer': 'B', 'explanation': 'Le comparatif de "big" est "bigger".', 'points': 10, 'difficulty_score': 0.4, 'confidence': 0.93},
                {'question': 'Quel est le superlatif de "good" ?', 'type': 'multiple_choice', 'option_a': 'gooder', 'option_b': 'goodest', 'option_c': 'best', 'option_d': 'more good', 'correct_answer': 'C', 'explanation': 'Le superlatif de "good" est "best".', 'points': 15, 'difficulty_score': 0.6, 'confidence': 0.92},
                {'question': 'Traduisez "Je vais à l\'école" en anglais.', 'type': 'multiple_choice', 'option_a': 'I go to school', 'option_b': 'I am go to school', 'option_c': 'I goes to school', 'option_d': 'I going to school', 'correct_answer': 'A', 'explanation': '"Je vais à l\'école" se traduit par "I go to school".', 'points': 10, 'difficulty_score': 0.3, 'confidence': 0.95},
            ]
        }

        # Récupérer les questions pour la matière
        subject_questions = questions_templates.get(subject.lower(), questions_templates['français'])

        # Sélectionner le nombre de questions demandé
        if len(subject_questions) >= num_questions:
            selected_questions = random.sample(subject_questions, num_questions)
        else:
            # Si pas assez de questions, répéter avec des variations
            selected_questions = subject_questions.copy()
            while len(selected_questions) < num_questions:
                selected_questions.extend(random.sample(subject_questions, min(num_questions - len(selected_questions), len(subject_questions))))

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
