"""
Générateur de feedback personnalisé par IA pour les évaluations
Utilise GPT pour analyser les performances et générer des recommandations adaptées
"""

import json
import random
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Avg, Q
from accounts.models import CustomUser
from gamification.models import UserProfile, QuizAttempt
from .models import EvaluationAttempt, StudentResponse, AIFeedback

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIFeedbackGenerator:
    """Générateur de feedback IA personnalisé"""

    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 1500

        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key

    def generate_feedback(self, attempt: EvaluationAttempt) -> AIFeedback:
        """
        Génère un feedback IA complet pour une tentative d'évaluation

        Args:
            attempt: L'objet EvaluationAttempt

        Returns:
            AIFeedback: Le feedback généré
        """
        # Analyser les réponses de l'étudiant
        analysis = self._analyze_student_responses(attempt)

        # Analyser le profil d'apprentissage
        profile_analysis = self._analyze_student_profile(attempt.student)

        # Générer le feedback avec IA
        if OPENAI_AVAILABLE and self.api_key:
            feedback_data = self._generate_ai_feedback(attempt, analysis, profile_analysis)
        else:
            feedback_data = self._generate_fallback_feedback(attempt, analysis, profile_analysis)

        # Formater le feedback en texte
        feedback_text = self._format_feedback_as_text(feedback_data)

        return feedback_text

    def _format_feedback_as_text(self, feedback_data: Dict[str, Any]) -> str:
        """
        Formate les données de feedback en texte lisible pour l'affichage
        """
        text_parts = []

        # Feedback général
        text_parts.append(f"## Analyse de votre performance\n\n{feedback_data['overall_feedback']}\n")

        # Points forts
        if feedback_data.get('strengths'):
            text_parts.append("## Vos points forts\n")
            for strength in feedback_data['strengths']:
                text_parts.append(f"✅ {strength['text']}")
            text_parts.append("")

        # Axes d'amélioration
        if feedback_data.get('improvements'):
            text_parts.append("## Axes d'amélioration\n")
            for improvement in feedback_data['improvements']:
                priority_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(improvement.get('priority', 'medium'), '🟡')
                text_parts.append(f"{priority_icon} {improvement['text']}")
            text_parts.append("")

        # Ressources recommandées
        if feedback_data.get('recommended_resources'):
            text_parts.append("## Ressources recommandées\n")
            for resource in feedback_data['recommended_resources']:
                text_parts.append(f"📚 **{resource['title']}**")
                text_parts.append(f"   *Type:* {resource.get('type', 'Non spécifié')}")
                text_parts.append(f"   *Pourquoi:* {resource.get('reason', 'À définir')}")
                if resource.get('url') and resource['url'] != 'lien ou description':
                    text_parts.append(f"   *Lien:* {resource['url']}")
                text_parts.append("")

        # Exercices recommandés
        if feedback_data.get('recommended_exercises'):
            text_parts.append("## Exercices recommandés\n")
            for exercise in feedback_data['recommended_exercises']:
                difficulty_icon = {
                    'facile': '🟢',
                    'moyen': '🟡',
                    'difficile': '🔴'
                }.get(exercise.get('difficulty', 'moyen'), '🟡')
                text_parts.append(f"{difficulty_icon} **{exercise['title']}**")
                text_parts.append(f"   *Type:* {exercise.get('type', 'Non spécifié')}")
                text_parts.append(f"   *Durée estimée:* {exercise.get('estimated_time', 'Non spécifiée')}")
                text_parts.append("")

        # Parcours d'apprentissage
        if feedback_data.get('learning_path'):
            text_parts.append("## Votre parcours d'apprentissage\n")
            for step in feedback_data['learning_path']:
                text_parts.append(f"🎯 {step}")
            text_parts.append("")

        return "\n".join(text_parts)

    def _analyze_student_responses(self, attempt: EvaluationAttempt) -> Dict[str, Any]:
        """
        Analyse détaillée des réponses de l'étudiant

        Returns:
            Dict avec statistiques et insights
        """
        responses = StudentResponse.objects.filter(
            student=attempt.student,
            evaluation=attempt.evaluation
        ).select_related('question')

        analysis = {
            'total_questions': responses.count(),
            'correct_count': 0,
            'incorrect_count': 0,
            'unanswered_count': 0,
            'question_types': {},
            'difficult_questions': [],
            'easy_questions': [],
            'time_per_question': 0,
            'response_patterns': [],
        }

        for response in responses:
            question_type = response.question.question_type

            # Compter par type de question
            if question_type not in analysis['question_types']:
                analysis['question_types'][question_type] = {
                    'total': 0, 'correct': 0, 'incorrect': 0
                }

            analysis['question_types'][question_type]['total'] += 1

            if response.is_correct is True:
                analysis['correct_count'] += 1
                analysis['question_types'][question_type]['correct'] += 1
            elif response.is_correct is False:
                analysis['incorrect_count'] += 1
                analysis['question_types'][question_type]['incorrect'] += 1
                # Ajouter aux questions difficiles
                analysis['difficult_questions'].append({
                    'question': response.question.text[:100],
                    'type': question_type,
                    'points': response.question.points
                })
            else:
                analysis['unanswered_count'] += 1

        # Calculer le temps moyen par question
        if attempt.time_elapsed and analysis['total_questions'] > 0:
            analysis['time_per_question'] = attempt.time_elapsed.total_seconds() / analysis['total_questions']

        # Identifier les patterns
        if analysis['incorrect_count'] > analysis['correct_count']:
            analysis['response_patterns'].append('difficultés générales')
        if analysis['question_types'].get('qcm', {}).get('correct', 0) < analysis['question_types'].get('qcm', {}).get('total', 1) * 0.7:
            analysis['response_patterns'].append('QCM à améliorer')
        if analysis['question_types'].get('open', {}).get('total', 0) > 0 and analysis['question_types'].get('open', {}).get('correct', 0) == 0:
            analysis['response_patterns'].append('questions ouvertes à développer')

        return analysis

    def _analyze_student_profile(self, student: CustomUser) -> Dict[str, Any]:
        """
        Analyse le profil d'apprentissage de l'étudiant

        Returns:
            Dict avec historique et préférences d'apprentissage
        """
        try:
            profile = student.gamification_profile
            profile_analysis = {
                'level': profile.level,
                'total_points': profile.total_points,
                'experience_points': profile.experience_points,
                'quizzes_completed': profile.quizzes_completed,
                'average_score': profile.average_score,
                'current_streak': profile.current_streak,
                'preferred_subjects': [s.name for s in profile.favorite_subjects.all()],
                'learning_style': self._infer_learning_style(profile),
            }
        except:
            profile_analysis = {
                'level': 1,
                'total_points': 0,
                'experience_points': 0,
                'quizzes_completed': 0,
                'average_score': 0.0,
                'current_streak': 0,
                'preferred_subjects': [],
                'learning_style': 'débutant',
            }

        # Analyser l'historique récent des quiz
        recent_attempts = QuizAttempt.objects.filter(
            student=student,
            completed_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-completed_at')[:10]

        profile_analysis['recent_performance'] = []
        for attempt in recent_attempts:
            profile_analysis['recent_performance'].append({
                'quiz_title': attempt.quiz.title,
                'score': attempt.percentage,
                'subject': attempt.quiz.subject.name,
                'completed_at': attempt.completed_at.isoformat(),
            })

        return profile_analysis

    def _infer_learning_style(self, profile) -> str:
        """Infère le style d'apprentissage basé sur les données du profil"""
        if profile.quizzes_completed < 5:
            return 'débutant'
        elif profile.average_score >= 80:
            return 'avancé'
        elif profile.current_streak >= 7:
            return 'discipliné'
        elif len(profile.favorite_subjects.all()) >= 3:
            return 'polyvalent'
        else:
            return 'intermédiaire'

    def _generate_ai_feedback(self, attempt: EvaluationAttempt, analysis: Dict, profile: Dict) -> Dict[str, Any]:
        """
        Génère le feedback en utilisant OpenAI GPT
        """
        try:
            # Préparer le prompt
            prompt = self._build_feedback_prompt(attempt, analysis, profile)

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un coach pédagogique expert qui analyse les performances des étudiants et fournit des feedbacks constructifs et personnalisés. Réponds en français."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
            )

            feedback_text = response.choices[0].message.content.strip()

            # Parser la réponse JSON
            try:
                feedback_data = json.loads(feedback_text)
                feedback_data['confidence_score'] = 0.9  # Confiance élevée pour GPT
                return feedback_data
            except json.JSONDecodeError:
                # Fallback si le parsing JSON échoue
                return self._parse_feedback_text(feedback_text, attempt.score_percentage)

        except Exception as e:
            print(f"Erreur lors de la génération IA: {e}")
            return self._generate_fallback_feedback(attempt, analysis, profile)

    def _build_feedback_prompt(self, attempt: EvaluationAttempt, analysis: Dict, profile: Dict) -> str:
        """Construit le prompt pour GPT"""

        score_pct = attempt.score_percentage
        evaluation_title = attempt.evaluation.title

        prompt = f"""
Analyse cette évaluation et génère un feedback personnalisé pour l'étudiant.

CONTEXTE DE L'ÉVALUATION:
- Titre: {evaluation_title}
- Score obtenu: {score_pct}%
- Questions totales: {analysis['total_questions']}
- Réponses correctes: {analysis['correct_count']}
- Réponses incorrectes: {analysis['incorrect_count']}

ANALYSE DES RÉPONSES:
- Types de questions: {json.dumps(analysis['question_types'], indent=2)}
- Temps moyen par question: {analysis.get('time_per_question', 0):.1f} secondes
- Patterns identifiés: {', '.join(analysis.get('response_patterns', []))}

PROFIL ÉTUDIANT:
- Niveau: {profile['level']}
- Quiz complétés: {profile['quizzes_completed']}
- Score moyen historique: {profile['average_score']}%
- Série actuelle: {profile['current_streak']} jours
- Style d'apprentissage: {profile['learning_style']}
- Matières préférées: {', '.join(profile['preferred_subjects'])}

INSTRUCTIONS:
Génère un feedback JSON avec cette structure exacte:
{{
    "overall_feedback": "Feedback général de 2-3 phrases",
    "performance_level": "excellent|very_good|good|satisfactory|needs_improvement",
    "strengths": [
        {{"text": "Point fort 1", "category": "concept|méthode|rapidité"}},
        {{"text": "Point fort 2", "category": "concept|méthode|rapidité"}}
    ],
    "improvements": [
        {{"text": "Point à améliorer 1", "priority": "high|medium|low", "category": "concept|méthode|pratique"}},
        {{"text": "Point à améliorer 2", "priority": "high|medium|low", "category": "concept|méthode|pratique"}}
    ],
    "recommended_resources": [
        {{"title": "Titre ressource", "type": "video|cours|article|exercice", "url": "lien ou description", "reason": "pourquoi recommandé"}},
        {{"title": "Titre ressource 2", "type": "video|cours|article|exercice", "url": "lien ou description", "reason": "pourquoi recommandé"}}
    ],
    "recommended_exercises": [
        {{"title": "Titre exercice", "type": "qcm|pratique|révision", "difficulty": "facile|moyen|difficile", "estimated_time": "15 min"}},
        {{"title": "Titre exercice 2", "type": "qcm|pratique|révision", "difficulty": "facile|moyen|difficile", "estimated_time": "15 min"}}
    ],
    "learning_path": [
        "Étape 1: Action concrète à faire",
        "Étape 2: Prochaine étape",
        "Étape 3: Objectif à moyen terme"
    ]
}}

Sois encourageant, spécifique et actionable. Adapte le feedback au niveau et au style d'apprentissage de l'étudiant.
"""

        return prompt

    def _parse_feedback_text(self, feedback_text: str, score_percentage: float) -> Dict[str, Any]:
        """Parse un feedback textuel en structure JSON"""
        # Logique de fallback pour parser le texte
        lines = feedback_text.split('\n')

        # Déterminer le niveau de performance
        if score_percentage >= 90:
            level = 'excellent'
        elif score_percentage >= 80:
            level = 'very_good'
        elif score_percentage >= 70:
            level = 'good'
        elif score_percentage >= 50:
            level = 'satisfactory'
        else:
            level = 'needs_improvement'

        return {
            'overall_feedback': feedback_text[:500],  # Premier paragraphe
            'performance_level': level,
            'strengths': [{'text': 'Analyse en cours', 'category': 'general'}],
            'improvements': [{'text': 'Feedback détaillé en préparation', 'priority': 'medium', 'category': 'general'}],
            'recommended_resources': [{'title': 'Ressources adaptées', 'type': 'mixed', 'url': 'À définir', 'reason': 'Basé sur votre profil'}],
            'recommended_exercises': [{'title': 'Exercices personnalisés', 'type': 'mixed', 'difficulty': 'adapté', 'estimated_time': '30 min'}],
            'learning_path': ['Continuer à pratiquer', 'Réviser les points faibles', 'Approfondir les connaissances'],
            'confidence_score': 0.6
        }

    def _detect_subject(self, evaluation_title: str) -> str:
        """
        Détecte le sujet de l'évaluation basé sur le titre
        """
        title_lower = evaluation_title.lower()

        # Mots-clés pour différents sujets
        subject_keywords = {
            'math': ['math', 'mathématiques', 'algèbre', 'géométrie', 'calcul', 'arithmétique'],
            'python': ['python', 'programmation', 'code', 'script', 'développement'],
            'science': ['physique', 'chimie', 'biologie', 'science', 'expérience'],
            'français': ['français', 'grammaire', 'littérature', 'orthographe', 'conjugaison'],
            'anglais': ['anglais', 'english', 'vocabulary', 'grammar'],
            'histoire': ['histoire', 'historique', 'civilisation', 'époque'],
            'géographie': ['géographie', 'carte', 'continent', 'pays']
        }

        for subject, keywords in subject_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return subject

        return 'general'  # Sujet général si non détecté

    def _get_subject_resources(self, subject: str, learning_style: str) -> List[Dict[str, str]]:
        """
        Retourne les ressources recommandées selon le sujet et le style d'apprentissage
        """
        resources_by_subject = {
            'math': {
                'débutant': [
                    {'title': 'Mathématiques pour Débutants - Khan Academy', 'type': 'video', 'url': 'https://www.khanacademy.org/math', 'reason': 'Cours interactifs gratuits pour apprendre les bases des maths'},
                    {'title': 'Exercices Mathématiques - Mathway', 'type': 'exercice', 'url': 'https://www.mathway.com/', 'reason': 'Outil pour résoudre des problèmes mathématiques étape par étape'},
                    {'title': 'Cours de Mathématiques - YouTube', 'type': 'video', 'url': 'https://www.youtube.com/results?search_query=cours+math+debutant', 'reason': 'Vidéos pédagogiques pour comprendre les concepts fondamentaux'}
                ],
                'avancé': [
                    {'title': 'Mathématiques Avancées - MIT OpenCourseWare', 'type': 'cours', 'url': 'https://ocw.mit.edu/courses/mathematics/', 'reason': 'Cours universitaires gratuits de mathématiques avancées'},
                    {'title': 'Problèmes Mathématiques Complexes - Project Euler', 'type': 'exercice', 'url': 'https://projecteuler.net/', 'reason': 'Défis mathématiques pour développer la logique et les compétences avancées'},
                    {'title': 'Articles Mathématiques - Wolfram', 'type': 'article', 'url': 'https://www.wolfram.com/mathematica/', 'reason': 'Ressources avancées pour l\'analyse mathématique'}
                ],
                'intermédiaire': [
                    {'title': 'Révisions Mathématiques - LeetCode Math', 'type': 'exercice', 'url': 'https://leetcode.com/problemset/all/', 'reason': 'Exercices mathématiques pour consolider les acquis'},
                    {'title': 'Cours Mathématiques Complets - Coursera', 'type': 'cours', 'url': 'https://www.coursera.org/browse/math-and-logic', 'reason': 'Formation structurée en mathématiques'},
                    {'title': 'Documentation Mathématique - Wolfram MathWorld', 'type': 'documentation', 'url': 'https://mathworld.wolfram.com/', 'reason': 'Encyclopédie mathématique complète'}
                ]
            },
            'python': {
                'débutant': [
                    {'title': 'Cours Python pour Débutants - FreeCodeCamp', 'type': 'video', 'url': 'https://www.youtube.com/watch?v=rfscVS0vtbw', 'reason': 'Tutoriel complet pour apprendre les bases de la programmation Python'},
                    {'title': 'Exercices Programmation - Codecademy', 'type': 'exercice', 'url': 'https://www.codecademy.com/learn/learn-python-3', 'reason': 'Pratique interactive avec exercices guidés en Python'},
                    {'title': 'Python pour les Nuls - YouTube', 'type': 'video', 'url': 'https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6pR7fWlcWJt0k6pXVX8-', 'reason': 'Série de vidéos pédagogiques pour débutants en Python'}
                ],
                'avancé': [
                    {'title': 'Design Patterns en Python - YouTube', 'type': 'video', 'url': 'https://www.youtube.com/watch?v=QNpwWkdFvgQ', 'reason': 'Approfondissement des concepts avancés de programmation Python'},
                    {'title': 'Projets Python Avancés - GitHub', 'type': 'projet', 'url': 'https://github.com/topics/python-project', 'reason': 'Exemples de projets complexes pour pratiquer Python avancé'},
                    {'title': 'Articles Techniques - Real Python', 'type': 'article', 'url': 'https://realpython.com/', 'reason': 'Tutoriels avancés et bonnes pratiques en Python'}
                ],
                'intermédiaire': [
                    {'title': 'Révisions Python Interactives - LeetCode', 'type': 'exercice', 'url': 'https://leetcode.com/problemset/all/', 'reason': 'Exercices de programmation Python pour consolider les acquis'},
                    {'title': 'Cours Python Complet - Coursera', 'type': 'cours', 'url': 'https://www.coursera.org/specializations/python', 'reason': 'Formation structurée avec certificats en Python'},
                    {'title': 'Documentation Python Officielle', 'type': 'documentation', 'url': 'https://docs.python.org/3/', 'reason': 'Référence complète pour les concepts Python intermédiaires'}
                ]
            },
            'science': {
                'débutant': [
                    {'title': 'Sciences pour Débutants - Khan Academy', 'type': 'video', 'url': 'https://www.khanacademy.org/science', 'reason': 'Cours interactifs gratuits pour découvrir les sciences'},
                    {'title': 'Expériences Scientifiques - YouTube', 'type': 'video', 'url': 'https://www.youtube.com/results?search_query=experiences+scientifiques+debutant', 'reason': 'Vidéos d\'expériences simples pour comprendre les concepts scientifiques'},
                    {'title': 'Quiz Sciences - National Geographic', 'type': 'exercice', 'url': 'https://www.nationalgeographic.com/', 'reason': 'Contenu éducatif et quiz sur la science'}
                ],
                'avancé': [
                    {'title': 'Sciences Avancées - edX', 'type': 'cours', 'url': 'https://www.edx.org/learn/science', 'reason': 'Cours universitaires en sciences avancées'},
                    {'title': 'Recherche Scientifique - ScienceDirect', 'type': 'article', 'url': 'https://www.sciencedirect.com/', 'reason': 'Articles de recherche scientifique peer-reviewed'},
                    {'title': 'Projets Scientifiques - GitHub Science', 'type': 'projet', 'url': 'https://github.com/topics/science', 'reason': 'Projets open-source en sciences'}
                ],
                'intermédiaire': [
                    {'title': 'Révisions Scientifiques - Coursera', 'type': 'cours', 'url': 'https://www.coursera.org/browse/physical-science-and-engineering', 'reason': 'Cours intermédiaires en sciences'},
                    {'title': 'Documentation Scientifique - Britannica', 'type': 'documentation', 'url': 'https://www.britannica.com/', 'reason': 'Encyclopédie scientifique complète'},
                    {'title': 'Exercices Scientifiques - PhET', 'type': 'exercice', 'url': 'https://phet.colorado.edu/', 'reason': 'Simulations interactives pour la physique, chimie et biologie'}
                ]
            },
            'general': {
                'débutant': [
                    {'title': 'Cours Généraux - Khan Academy', 'type': 'video', 'url': 'https://www.khanacademy.org/', 'reason': 'Plateforme éducative gratuite avec cours dans toutes les matières'},
                    {'title': 'Exercices Interactifs - Duolingo', 'type': 'exercice', 'url': 'https://www.duolingo.com/', 'reason': 'Apprentissage ludique et interactif'},
                    {'title': 'Vidéos Éducatives - TED-Ed', 'type': 'video', 'url': 'https://ed.ted.com/', 'reason': 'Vidéos pédagogiques sur divers sujets'}
                ],
                'avancé': [
                    {'title': 'Cours Avancés - Coursera', 'type': 'cours', 'url': 'https://www.coursera.org/', 'reason': 'Cours universitaires dans toutes les disciplines'},
                    {'title': 'Articles Académiques - Google Scholar', 'type': 'article', 'url': 'https://scholar.google.com/', 'reason': 'Recherche d\'articles scientifiques et académiques'},
                    {'title': 'Projets Open-Source - GitHub', 'type': 'projet', 'url': 'https://github.com/', 'reason': 'Collaboration sur des projets complexes'}
                ],
                'intermédiaire': [
                    {'title': 'Révisions Générales - edX', 'type': 'cours', 'url': 'https://www.edx.org/', 'reason': 'Cours en ligne de qualité universitaire'},
                    {'title': 'Documentation - Wikipedia', 'type': 'documentation', 'url': 'https://www.wikipedia.org/', 'reason': 'Encyclopédie collaborative et complète'},
                    {'title': 'Exercices Pratiques - Codecademy', 'type': 'exercice', 'url': 'https://www.codecademy.com/', 'reason': 'Pratique interactive dans diverses matières'}
                ]
            }
        }

        # Utiliser 'general' comme fallback si le sujet n'est pas trouvé
        subject_resources = resources_by_subject.get(subject, resources_by_subject['general'])
        return subject_resources.get(learning_style, subject_resources['intermédiaire'])

    def _generate_fallback_feedback(self, attempt: EvaluationAttempt, analysis: Dict, profile: Dict) -> Dict[str, Any]:
        """
        Génère un feedback de fallback basé sur des règles heuristiques
        """
        score_pct = attempt.score_percentage

        # Déterminer le niveau de performance
        if score_pct >= 90:
            level = 'excellent'
            overall = "Excellent travail ! Vous maîtrisez parfaitement le sujet."
        elif score_pct >= 80:
            level = 'very_good'
            overall = "Très bon travail ! Vous avez bien compris les concepts principaux."
        elif score_pct >= 70:
            level = 'good'
            overall = "Bon travail ! Vous avez les bases solides, quelques révisions seraient bénéfiques."
        elif score_pct >= 50:
            level = 'satisfactory'
            overall = "Travail satisfaisant. Des révisions supplémentaires sont recommandées pour consolider vos connaissances."
        else:
            level = 'needs_improvement'
            overall = "Des efforts supplémentaires sont nécessaires. N'hésitez pas à demander de l'aide pour mieux comprendre les concepts."

        # Générer des points forts et améliorations basés sur l'analyse
        strengths = []
        improvements = []

        if analysis['correct_count'] > analysis['total_questions'] * 0.7:
            strengths.append({'text': 'Bonne compréhension générale du sujet', 'category': 'concept'})

        if analysis.get('time_per_question', 0) < 120:  # Moins de 2 min par question
            strengths.append({'text': 'Rapidité dans les réponses', 'category': 'méthode'})

        if analysis['incorrect_count'] > 0:
            improvements.append({
                'text': f'Améliorer la compréhension de {len(analysis["difficult_questions"])} concepts spécifiques',
                'priority': 'high',
                'category': 'concept'
            })

        # Détecter le sujet de l'évaluation
        subject = self._detect_subject(attempt.evaluation.title)
        learning_style = profile.get('learning_style', 'intermédiaire')

        # Recommandations basées sur le sujet et le profil d'apprentissage
        recommended_resources = self._get_subject_resources(subject, learning_style)

        recommended_exercises = [
            {'title': 'Quiz de révision ciblé', 'type': 'qcm', 'difficulty': 'moyen', 'estimated_time': '20 min'},
            {'title': 'Exercices pratiques', 'type': 'pratique', 'difficulty': 'adapté', 'estimated_time': '30 min'}
        ]

        learning_path = [
            "1. Identifier et réviser les concepts mal maîtrisés",
            "2. Pratiquer régulièrement avec des exercices similaires",
            "3. Approfondir les sujets d'intérêt pour maintenir la motivation"
        ]

        return {
            'overall_feedback': overall,
            'performance_level': level,
            'strengths': strengths,
            'improvements': improvements,
            'recommended_resources': recommended_resources,
            'recommended_exercises': recommended_exercises,
            'learning_path': learning_path,
            'confidence_score': 0.7
        }


# Fonction utilitaire pour générer le feedback
def generate_student_feedback(attempt: EvaluationAttempt) -> AIFeedback:
    """
    Fonction principale pour générer le feedback IA d'un étudiant

    Args:
        attempt: La tentative d'évaluation terminée

    Returns:
        AIFeedback: Le feedback généré
    """
    generator = AIFeedbackGenerator()
    return generator.generate_feedback(attempt)
