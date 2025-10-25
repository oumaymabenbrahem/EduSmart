#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la génération des questions du quiz
"""

import os
import sys
import django

# Configurer l'encodage
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from gamification.ai_quiz_generator import AIQuizGenerator
from gamification.models import UserProfile, Quiz, Question
from accounts.models import CustomUser

def test_quiz_generation():
    """Test la génération d'un quiz avec plusieurs questions"""

    print("=" * 80)
    print("TEST DE GÉNÉRATION DE QUIZ")
    print("=" * 80)

    # Créer un utilisateur de test
    user, created = CustomUser.objects.get_or_create(
        username='test_teacher',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'Teacher'}
    )
    
    # Créer le profil de gamification
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Créer le générateur
    generator = AIQuizGenerator()
    
    # Nettoyer les anciens quiz générés
    Quiz.objects.filter(is_ai_generated=True).delete()

    # Test 1: Générer un quiz en Français avec 10 questions
    print("\n📚 Test 1: Génération d'un quiz en Français (10 questions)")
    print("-" * 80)
    quiz_fr = generator.generate_quiz('Français', difficulty_level=2, num_questions=10, user_profile=user_profile)
    
    if quiz_fr:
        print(f"✅ Quiz créé: {quiz_fr.title}")
        print(f"   ID: {quiz_fr.id}")
        print(f"   Sujet: {quiz_fr.subject.name}")
        print(f"   Difficulté: {quiz_fr.difficulty.name}")
        print(f"   Nombre de questions: {quiz_fr.questions.count()}")
        print(f"   Points disponibles: {quiz_fr.points_available}")
        print(f"   Temps limite: {quiz_fr.time_limit} minutes")
        
        # Afficher les questions
        print("\n   Questions du quiz:")
        for i, question in enumerate(quiz_fr.questions.all(), 1):
            print(f"\n   Q{i}: {question.question_text}")
            print(f"       A) {question.option_a}")
            print(f"       B) {question.option_b}")
            print(f"       C) {question.option_c}")
            print(f"       D) {question.option_d}")
            print(f"       ✓ Réponse correcte: {question.correct_answer}")
            print(f"       💡 Explication: {question.explanation}")
            print(f"       Points: {question.points}")
    else:
        print("❌ Erreur lors de la génération du quiz")
    
    # Test 2: Générer un quiz en Mathématiques avec 8 questions
    print("\n\n📚 Test 2: Génération d'un quiz en Mathématiques (8 questions)")
    print("-" * 80)
    quiz_math = generator.generate_quiz('Mathématiques', difficulty_level=3, num_questions=8, user_profile=user_profile)

    if quiz_math:
        print(f"✅ Quiz créé: {quiz_math.title}")
        print(f"   ID: {quiz_math.id}")
        print(f"   Sujet: {quiz_math.subject.name}")
        print(f"   Difficulté: {quiz_math.difficulty.name}")
        print(f"   Nombre de questions: {quiz_math.questions.count()}")
        print(f"   Points disponibles: {quiz_math.points_available}")
        print(f"   Temps limite: {quiz_math.time_limit} minutes")

        # Afficher les questions
        print("\n   Questions du quiz:")
        for i, question in enumerate(quiz_math.questions.all(), 1):
            print(f"\n   Q{i}: {question.question_text}")
            print(f"       A) {question.option_a}")
            print(f"       B) {question.option_b}")
            print(f"       C) {question.option_c}")
            print(f"       D) {question.option_d}")
            print(f"       Reponse correcte: {question.correct_answer}")
            print(f"       Explication: {question.explanation}")
            print(f"       Points: {question.points}")
    else:
        print("❌ Erreur lors de la génération du quiz")

    # Test 3: Générer un quiz en Informatique avec 12 questions
    print("\n\n📚 Test 3: Génération d'un quiz en Informatique (12 questions)")
    print("-" * 80)
    quiz_info = generator.generate_quiz('Informatique', difficulty_level=4, num_questions=12, user_profile=user_profile)

    if quiz_info:
        print(f"✅ Quiz créé: {quiz_info.title}")
        print(f"   ID: {quiz_info.id}")
        print(f"   Sujet: {quiz_info.subject.name}")
        print(f"   Difficulté: {quiz_info.difficulty.name}")
        print(f"   Nombre de questions: {quiz_info.questions.count()}")
        print(f"   Points disponibles: {quiz_info.points_available}")
        print(f"   Temps limite: {quiz_info.time_limit} minutes")

        # Afficher les questions
        print("\n   Questions du quiz:")
        for i, question in enumerate(quiz_info.questions.all(), 1):
            print(f"\n   Q{i}: {question.question_text}")
            print(f"       A) {question.option_a}")
            print(f"       B) {question.option_b}")
            print(f"       C) {question.option_c}")
            print(f"       D) {question.option_d}")
            print(f"       Reponse correcte: {question.correct_answer}")
            print(f"       Explication: {question.explanation}")
            print(f"       Points: {question.points}")
    else:
        print("❌ Erreur lors de la génération du quiz")

    # Test 4: Générer un quiz en Anglais avec 15 questions
    print("\n\n📚 Test 4: Génération d'un quiz en Anglais (15 questions)")
    print("-" * 80)
    quiz_en = generator.generate_quiz('Anglais', difficulty_level=2, num_questions=15, user_profile=user_profile)
    
    if quiz_en:
        print(f"✅ Quiz créé: {quiz_en.title}")
        print(f"   ID: {quiz_en.id}")
        print(f"   Sujet: {quiz_en.subject.name}")
        print(f"   Difficulté: {quiz_en.difficulty.name}")
        print(f"   Nombre de questions: {quiz_en.questions.count()}")
        print(f"   Points disponibles: {quiz_en.points_available}")
        print(f"   Temps limite: {quiz_en.time_limit} minutes")
        
        # Afficher les questions
        print("\n   Questions du quiz (affichage des 5 premières):")
        for i, question in enumerate(quiz_en.questions.all()[:5], 1):
            print(f"\n   Q{i}: {question.question_text}")
            print(f"       A) {question.option_a}")
            print(f"       B) {question.option_b}")
            print(f"       C) {question.option_c}")
            print(f"       D) {question.option_d}")
            print(f"       ✓ Réponse correcte: {question.correct_answer}")
            print(f"       💡 Explication: {question.explanation}")
            print(f"       Points: {question.points}")
        
        print(f"\n   ... et {quiz_en.questions.count() - 5} autres questions")
    else:
        print("❌ Erreur lors de la génération du quiz")
    
    # Résumé
    print("\n\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    total_quizzes = Quiz.objects.filter(is_ai_generated=True).count()
    total_questions = Question.objects.filter(is_ai_generated=True).count()
    
    print(f"\n✅ Total de quiz générés: {total_quizzes}")
    print(f"✅ Total de questions générées: {total_questions}")
    print(f"✅ Moyenne de questions par quiz: {total_questions / total_quizzes if total_quizzes > 0 else 0:.1f}")
    
    print("\n" + "=" * 80)
    print("✅ TOUS LES TESTS SONT TERMINÉS!")
    print("=" * 80)

if __name__ == '__main__':
    test_quiz_generation()

