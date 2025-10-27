"""
Système de gamification avancé et innovant pour EduSmart
Fonctionnalités:
- Système de quêtes et missions
- Récompenses dynamiques
- Analyse comportementale
- Recommandations personnalisées
- Système de guildes/équipes
- Défis temporaires
"""

import json
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from django.core.cache import cache
from .models import *
from .ai_quiz_generator import AIQuizGenerator


class AdvancedGamificationEngine:
    """Moteur de gamification avancé avec IA"""
    
    def __init__(self):
        self.ai_generator = AIQuizGenerator()
    
    def generate_personalized_quiz(self, user_profile):
        """Génère un quiz personnalisé basé sur le profil utilisateur"""
        # Analyser les performances passées
        weak_subjects = self._analyze_weak_subjects(user_profile)
        preferred_difficulty = self._calculate_optimal_difficulty(user_profile)
        
        # Choisir le sujet à améliorer
        if weak_subjects:
            subject = random.choice(weak_subjects)
        else:
            subject = random.choice(['français', 'mathématiques', 'informatique', 'anglais'])
        
        # Générer le quiz adaptatif
        quiz = self.ai_generator.generate_quiz(
            subject_name=subject,
            difficulty_level=preferred_difficulty,
            num_questions=10,
            user_profile=user_profile
        )
        
        return quiz
    
    def _analyze_weak_subjects(self, user_profile):
        """Analyse les matières où l'utilisateur a des difficultés"""
        attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).select_related('quiz__subject')
        
        subject_scores = {}
        for attempt in attempts:
            subject = attempt.quiz.subject.name
            if subject not in subject_scores:
                subject_scores[subject] = []
            subject_scores[subject].append(attempt.percentage)
        
        # Identifier les matières avec score moyen < 70%
        weak_subjects = []
        for subject, scores in subject_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 70:
                weak_subjects.append(subject)
        
        return weak_subjects
    
    def _calculate_optimal_difficulty(self, user_profile):
        """Calcule le niveau de difficulté optimal"""
        recent_attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed',
            completed_at__gte=timezone.now() - timedelta(days=7)
        )
        
        if not recent_attempts.exists():
            return 2  # Niveau moyen par défaut
        
        avg_score = recent_attempts.aggregate(Avg('percentage'))['percentage__avg']
        
        if avg_score >= 90:
            return min(5, user_profile.level + 1)
        elif avg_score >= 80:
            return user_profile.level
        elif avg_score >= 70:
            return max(1, user_profile.level - 1)
        else:
            return max(1, user_profile.level - 2)


class QuestSystem:
    """Système de quêtes et missions"""
    
    QUEST_TYPES = {
        'daily': {
            'complete_quiz': {
                'name': 'Quiz Quotidien',
                'description': 'Complétez un quiz aujourd\'hui',
                'reward_points': 50,
                'reward_exp': 25
            },
            'perfect_score': {
                'name': 'Score Parfait',
                'description': 'Obtenez 100% à un quiz',
                'reward_points': 200,
                'reward_exp': 100
            },
            'speed_demon': {
                'name': 'Démon de Vitesse',
                'description': 'Terminez un quiz en moins de 5 minutes',
                'reward_points': 150,
                'reward_exp': 75
            }
        },
        'weekly': {
            'quiz_master': {
                'name': 'Maître des Quiz',
                'description': 'Complétez 10 quiz cette semaine',
                'reward_points': 500,
                'reward_exp': 250
            },
            'subject_explorer': {
                'name': 'Explorateur de Matières',
                'description': 'Essayez 3 matières différentes',
                'reward_points': 300,
                'reward_exp': 150
            }
        },
        'achievement': {
            'first_steps': {
                'name': 'Premiers Pas',
                'description': 'Complétez votre premier quiz',
                'reward_points': 100,
                'reward_exp': 50
            },
            'century_club': {
                'name': 'Club des Centenaires',
                'description': 'Complétez 100 quiz',
                'reward_points': 2000,
                'reward_exp': 1000
            }
        }
    }
    
    def check_quest_completion(self, user_profile, quest_type='all'):
        """Vérifie et complète les quêtes"""
        completed_quests = []
        
        if quest_type in ['all', 'daily']:
            completed_quests.extend(self._check_daily_quests(user_profile))
        
        if quest_type in ['all', 'weekly']:
            completed_quests.extend(self._check_weekly_quests(user_profile))
        
        if quest_type in ['all', 'achievement']:
            completed_quests.extend(self._check_achievement_quests(user_profile))
        
        return completed_quests
    
    def _check_weekly_quests(self, user_profile):
        """Vérifie les quêtes hebdomadaires"""
        week_ago = timezone.now() - timedelta(days=7)
        completed = []
        
        # Quiz master - 10 quiz cette semaine
        weekly_attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            started_at__gte=week_ago,
            status='completed'
        )
        
        if weekly_attempts.count() >= 10:
            quest_key = f"weekly_quiz_master_{user_profile.user.id}_{week_ago.strftime('%Y-%W')}"
            if not cache.get(quest_key):
                completed.append(self.QUEST_TYPES['weekly']['quiz_master'])
                cache.set(quest_key, True, 604800)  # 7 jours
        
        # Explorateur de matières - 3 matières différentes
        subjects_tried = weekly_attempts.values_list('quiz__subject', flat=True).distinct()
        if subjects_tried.count() >= 3:
            quest_key = f"weekly_subject_explorer_{user_profile.user.id}_{week_ago.strftime('%Y-%W')}"
            if not cache.get(quest_key):
                completed.append(self.QUEST_TYPES['weekly']['subject_explorer'])
                cache.set(quest_key, True, 604800)
        
        return completed
    
    def _check_achievement_quests(self, user_profile):
        """Vérifie les quêtes de réalisation"""
        completed = []
        
        # Premiers pas
        if user_profile.quizzes_completed >= 1:
            quest_key = f"achievement_first_steps_{user_profile.user.id}"
            if not cache.get(quest_key):
                completed.append(self.QUEST_TYPES['achievement']['first_steps'])
                cache.set(quest_key, True, None)  # Permanent
        
        # Club des centenaires
        if user_profile.quizzes_completed >= 100:
            quest_key = f"achievement_century_club_{user_profile.user.id}"
            if not cache.get(quest_key):
                completed.append(self.QUEST_TYPES['achievement']['century_club'])
                cache.set(quest_key, True, None)  # Permanent
        
        return completed
    
    def _check_daily_quests(self, user_profile):
        """Vérifie les quêtes quotidiennes"""
        today = timezone.now().date()
        completed = []
        
        # Quiz quotidien
        daily_attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            started_at__date=today,
            status='completed'
        )
        
        if daily_attempts.exists():
            quest_key = f"daily_complete_quiz_{user_profile.user.id}_{today}"
            if not cache.get(quest_key):
                completed.append(self.QUEST_TYPES['daily']['complete_quiz'])
                cache.set(quest_key, True, 86400)  # 24h
        
        # Score parfait
        perfect_attempts = daily_attempts.filter(percentage=100.0)
        if perfect_attempts.exists():
            quest_key = f"daily_perfect_score_{user_profile.user.id}_{today}"
            if not cache.get(quest_key):
                completed.append(self.QUEST_TYPES['daily']['perfect_score'])
                cache.set(quest_key, True, 86400)
        
        return completed


class RewardSystem:
    """Système de récompenses dynamiques"""
    
    def calculate_dynamic_rewards(self, quiz_attempt):
        """Calcule les récompenses basées sur la performance"""
        base_points = quiz_attempt.quiz.points_available
        base_exp = quiz_attempt.quiz.experience_points
        
        # Multiplicateurs basés sur la performance
        performance_multiplier = self._get_performance_multiplier(quiz_attempt.percentage)
        difficulty_multiplier = quiz_attempt.quiz.difficulty.points_multiplier
        speed_multiplier = self._get_speed_multiplier(quiz_attempt)
        streak_multiplier = self._get_streak_multiplier(quiz_attempt.student)
        
        # Calcul final
        final_points = int(base_points * performance_multiplier * difficulty_multiplier * speed_multiplier * streak_multiplier)
        final_exp = int(base_exp * performance_multiplier * difficulty_multiplier * speed_multiplier * streak_multiplier)
        
        return {
            'points': final_points,
            'experience': final_exp,
            'multipliers': {
                'performance': performance_multiplier,
                'difficulty': difficulty_multiplier,
                'speed': speed_multiplier,
                'streak': streak_multiplier
            }
        }
    
    def _get_performance_multiplier(self, percentage):
        """Multiplicateur basé sur le score"""
        if percentage >= 95:
            return 2.0
        elif percentage >= 90:
            return 1.8
        elif percentage >= 80:
            return 1.5
        elif percentage >= 70:
            return 1.2
        elif percentage >= 60:
            return 1.0
        else:
            return 0.8
    
    def _get_speed_multiplier(self, quiz_attempt):
        """Multiplicateur basé sur la vitesse"""
        time_limit = quiz_attempt.quiz.time_limit * 60  # en secondes
        time_taken = quiz_attempt.time_taken
        
        if time_taken <= time_limit * 0.5:  # Moins de 50% du temps
            return 1.5
        elif time_taken <= time_limit * 0.75:  # Moins de 75% du temps
            return 1.2
        else:
            return 1.0
    
    def _get_streak_multiplier(self, user):
        """Multiplicateur basé sur la série"""
        profile = user.gamification_profile
        streak = profile.current_streak
        
        if streak >= 30:
            return 2.0
        elif streak >= 14:
            return 1.8
        elif streak >= 7:
            return 1.5
        elif streak >= 3:
            return 1.2
        else:
            return 1.0


class PersonalizedRecommendationEngine:
    """Moteur de recommandations personnalisées"""
    
    def get_recommendations(self, user_profile):
        """Génère des recommandations personnalisées"""
        recommendations = {
            'quizzes': self._recommend_quizzes(user_profile),
            'subjects': self._recommend_subjects(user_profile),
            'difficulty': self._recommend_difficulty(user_profile),
            'study_plan': self._generate_study_plan(user_profile)
        }
        
        return recommendations
    
    def _recommend_quizzes(self, user_profile):
        """Recommande des quiz spécifiques"""
        # Analyser l'historique
        completed_quizzes = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).values_list('quiz_id', flat=True)
        
        # Recommander des quiz non complétés dans les matières préférées
        recommended = Quiz.objects.filter(
            status='published'
        ).exclude(
            id__in=completed_quizzes
        ).select_related('subject', 'difficulty')
        
        # Filtrer par matières préférées si disponibles
        if user_profile.favorite_subjects.exists():
            recommended = recommended.filter(
                subject__in=user_profile.favorite_subjects.all()
            )
        
        return recommended[:5]
    
    def _recommend_subjects(self, user_profile):
        """Recommande des matières à explorer"""
        # Analyser les matières déjà essayées
        tried_subjects = QuizAttempt.objects.filter(
            student=user_profile.user
        ).values_list('quiz__subject', flat=True).distinct()
        
        # Recommander de nouvelles matières
        new_subjects = Subject.objects.exclude(
            id__in=tried_subjects
        ).filter(is_active=True)
        
        return new_subjects[:3]
    
    def _recommend_difficulty(self, user_profile):
        """Recommande un niveau de difficulté optimal"""
        # Analyser les performances récentes
        recent_attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).order_by('-completed_at')[:10]
        
        if not recent_attempts.exists():
            return {
                'recommended_level': 2,
                'reason': 'Niveau débutant recommandé pour commencer'
            }
        
        # Calculer le score moyen récent
        avg_score = sum(attempt.percentage for attempt in recent_attempts) / len(recent_attempts)
        
        # Recommander le niveau basé sur la performance
        if avg_score >= 90:
            recommended_level = min(5, user_profile.level + 1)
            reason = "Excellent ! Essayez un niveau plus difficile"
        elif avg_score >= 80:
            recommended_level = user_profile.level
            reason = "Continuez à ce niveau, vous maîtrisez bien"
        elif avg_score >= 70:
            recommended_level = user_profile.level
            reason = "Niveau actuel approprié, continuez à vous améliorer"
        elif avg_score >= 60:
            recommended_level = max(1, user_profile.level - 1)
            reason = "Essayez un niveau plus facile pour consolider vos bases"
        else:
            recommended_level = max(1, user_profile.level - 2)
            reason = "Revenez aux bases pour mieux progresser"
        
        return {
            'recommended_level': recommended_level,
            'current_performance': avg_score,
            'reason': reason
        }
    
    def _generate_study_plan(self, user_profile):
        """Génère un plan d'étude personnalisé"""
        weak_areas = self._identify_weak_areas(user_profile)
        
        plan = {
            'daily_goals': {
                'quizzes': 2,
                'points': 200,
                'time_minutes': 30
            },
            'weekly_goals': {
                'quizzes': 10,
                'new_subjects': 1,
                'perfect_scores': 2
            },
            'focus_areas': weak_areas,
            'recommended_schedule': self._create_schedule(user_profile)
        }
        
        return plan
    
    def _create_schedule(self, user_profile):
        """Crée un planning d'étude personnalisé"""
        from datetime import datetime, timedelta
        
        # Analyser les habitudes d'étude de l'utilisateur
        recent_attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).order_by('-completed_at')[:20]
        
        # Calculer les créneaux préférés
        preferred_hours = []
        if recent_attempts.exists():
            for attempt in recent_attempts:
                hour = attempt.completed_at.hour
                preferred_hours.append(hour)
        
        # Déterminer le créneau le plus fréquent
        if preferred_hours:
            most_common_hour = max(set(preferred_hours), key=preferred_hours.count)
        else:
            most_common_hour = 18  # 18h par défaut
        
        # Générer un planning pour la semaine
        schedule = {
            'weekly_sessions': [],
            'daily_goals': {
                'duration_minutes': 30,
                'quizzes_target': 2,
                'points_target': 200
            },
            'preferred_time': f"{most_common_hour}:00",
            'rest_days': ['dimanche']  # Jour de repos recommandé
        }
        
        # Créer les sessions de la semaine
        days = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']
        weak_areas = self._identify_weak_areas(user_profile)
        
        for i, day in enumerate(days):
            if weak_areas and i < len(weak_areas):
                focus_subject = weak_areas[i]['subject']
            else:
                focus_subject = "Révision générale"
            
            session = {
                'day': day,
                'time': f"{most_common_hour}:00",
                'duration': 30,
                'focus': focus_subject,
                'difficulty': 'adaptatif',
                'type': 'quiz_practice' if i % 2 == 0 else 'review'
            }
            schedule['weekly_sessions'].append(session)
        
        return schedule
    
    def _identify_weak_areas(self, user_profile):
        """Identifie les domaines à améliorer"""
        attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).select_related('quiz__subject')
        
        subject_performance = {}
        for attempt in attempts:
            subject = attempt.quiz.subject.name
            if subject not in subject_performance:
                subject_performance[subject] = []
            subject_performance[subject].append(attempt.percentage)
        
        weak_areas = []
        for subject, scores in subject_performance.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 75:
                weak_areas.append({
                    'subject': subject,
                    'average_score': avg_score,
                    'improvement_needed': 75 - avg_score
                })
        
        return sorted(weak_areas, key=lambda x: x['improvement_needed'], reverse=True)


class SocialGamificationFeatures:
    """Fonctionnalités sociales de gamification"""
    
    def create_challenge(self, creator, title, description, quiz, duration_days=7):
        """Crée un défi entre utilisateurs"""
        # Cette fonctionnalité nécessiterait un modèle Challenge
        # Pour l'instant, on simule la création
        challenge_data = {
            'title': title,
            'description': description,
            'creator': creator.username,
            'quiz_id': quiz.id,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=duration_days),
            'participants': [],
            'leaderboard': []
        }
        
        return challenge_data
    
    def get_friend_activities(self, user):
        """Récupère les activités des amis (simulation)"""
        # Cette fonctionnalité nécessiterait un système d'amis
        recent_activities = QuizAttempt.objects.filter(
            status='completed',
            completed_at__gte=timezone.now() - timedelta(days=7)
        ).exclude(student=user).select_related('student', 'quiz')[:10]
        
        activities = []
        for attempt in recent_activities:
            activities.append({
                'user': attempt.student.username,
                'action': f'a complété le quiz "{attempt.quiz.title}"',
                'score': f'{attempt.percentage}%',
                'time': attempt.completed_at
            })
        
        return activities


class AnalyticsEngine:
    """Moteur d'analyse et de statistiques avancées"""
    
    def generate_user_analytics(self, user_profile):
        """Génère des analyses détaillées pour un utilisateur"""
        analytics = {
            'performance_trends': self._calculate_performance_trends(user_profile),
            'subject_mastery': self._calculate_subject_mastery(user_profile),
            'learning_patterns': self._analyze_learning_patterns(user_profile),
            'predictions': self._predict_future_performance(user_profile)
        }
        
        return analytics
    
    def _calculate_performance_trends(self, user_profile):
        """Calcule les tendances de performance"""
        attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).order_by('completed_at')
        
        if attempts.count() < 5:
            return {'trend': 'insufficient_data'}
        
        recent_scores = list(attempts.values_list('percentage', flat=True)[-10:])
        older_scores = list(attempts.values_list('percentage', flat=True)[-20:-10])
        
        if not older_scores:
            return {'trend': 'improving', 'confidence': 'low'}
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        improvement = recent_avg - older_avg
        
        if improvement > 5:
            trend = 'improving'
        elif improvement < -5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'improvement': improvement,
            'recent_average': recent_avg,
            'confidence': 'high' if len(recent_scores) >= 8 else 'medium'
        }
    
    def _calculate_subject_mastery(self, user_profile):
        """Calcule la maîtrise par matière"""
        attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).select_related('quiz__subject')
        
        subject_mastery = {}
        for attempt in attempts:
            subject_name = attempt.quiz.subject.name
            try:
                subject = Subject.objects.get(name=subject_name)
            except Subject.DoesNotExist:
                subject = Subject.objects.create(
                    name=subject_name,
                    description=f'Quiz sur {subject_name}',
                    icon='bi-book',
                    color=self._get_subject_color(subject_name)
                )
            
            if subject not in subject_mastery:
                subject_mastery[subject] = {
                    'scores': [],
                    'total_attempts': 0,
                    'recent_scores': []
                }
            
            subject_mastery[subject]['scores'].append(attempt.percentage)
            subject_mastery[subject]['total_attempts'] += 1
            
            # Garder les 5 derniers scores
            if len(subject_mastery[subject]['recent_scores']) >= 5:
                subject_mastery[subject]['recent_scores'].pop(0)
            subject_mastery[subject]['recent_scores'].append(attempt.percentage)
        
        # Calculer les statistiques finales
        for subject, data in subject_mastery.items():
            data['average_score'] = sum(data['scores']) / len(data['scores'])
            data['recent_average'] = sum(data['recent_scores']) / len(data['recent_scores'])
            data['mastery_level'] = self._get_mastery_level(data['average_score'])
        
        return subject_mastery
    
    def _analyze_learning_patterns(self, user_profile):
        """Analyse les patterns d'apprentissage"""
        attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).order_by('completed_at')
        
        if attempts.count() < 3:
            return {'pattern': 'insufficient_data'}
        
        # Analyser les heures d'activité
        activity_hours = []
        for attempt in attempts:
            activity_hours.append(attempt.completed_at.hour)
        
        # Trouver l'heure la plus fréquente
        from collections import Counter
        hour_counts = Counter(activity_hours)
        peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 12
        
        # Analyser la régularité
        dates = [attempt.completed_at.date() for attempt in attempts]
        unique_dates = len(set(dates))
        total_days = (attempts.last().completed_at.date() - attempts.first().completed_at.date()).days + 1
        regularity = unique_dates / total_days if total_days > 0 else 0
        
        return {
            'peak_hour': peak_hour,
            'regularity': regularity,
            'total_sessions': attempts.count(),
            'pattern': 'regular' if regularity > 0.3 else 'irregular'
        }
    
    def _predict_future_performance(self, user_profile):
        """Prédit les performances futures"""
        attempts = QuizAttempt.objects.filter(
            student=user_profile.user,
            status='completed'
        ).order_by('completed_at')
        
        if attempts.count() < 5:
            return {'prediction': 'insufficient_data'}
        
        # Prendre les 10 derniers scores
        recent_scores = list(attempts.values_list('percentage', flat=True)[-10:])
        
        # Calcul de tendance simple
        if len(recent_scores) >= 5:
            first_half = recent_scores[:len(recent_scores)//2]
            second_half = recent_scores[len(recent_scores)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            trend = second_avg - first_avg
            
            # Prédiction basée sur la tendance
            current_avg = sum(recent_scores) / len(recent_scores)
            predicted_score = max(0, min(100, current_avg + trend))
            
            return {
                'predicted_score': predicted_score,
                'trend': trend,
                'confidence': 'medium',
                'recommendation': self._get_performance_recommendation(predicted_score, trend)
            }
        
        return {'prediction': 'insufficient_data'}
    
    def _get_mastery_level(self, average_score):
        """Détermine le niveau de maîtrise basé sur le score moyen"""
        if average_score >= 90:
            return 'expert'
        elif average_score >= 80:
            return 'advanced'
        elif average_score >= 70:
            return 'intermediate'
        elif average_score >= 60:
            return 'beginner'
        else:
            return 'novice'
    
    def _get_performance_recommendation(self, predicted_score, trend):
        """Génère une recommandation basée sur la performance prédite"""
        if predicted_score >= 85 and trend > 0:
            return "Excellente progression ! Continuez sur cette lancée."
        elif predicted_score >= 75 and trend > 0:
            return "Bonne amélioration. Essayez des quiz plus difficiles."
        elif trend < -5:
            return "Performance en baisse. Prenez une pause et révisez les bases."
        elif predicted_score < 60:
            return "Concentrez-vous sur les matières les plus faibles."
        else:
            return "Performance stable. Variez les sujets pour progresser."
    
    def _get_subject_color(self, subject_name):
        """Retourne une couleur associée à une matière"""
        colors = {
            'français': '#e74c3c',
            'mathématiques': '#3498db',
            'informatique': '#9b59b6',
            'anglais': '#2ecc71',
            'histoire': '#f39c12',
            'sciences': '#1abc9c',
            'physique': '#34495e',
            'chimie': '#e67e22',
            'biologie': '#27ae60',
            'géographie': '#8e44ad'
        }
        return colors.get(subject_name.lower(), '#95a5a6')
