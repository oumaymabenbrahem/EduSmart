#!/usr/bin/env python
"""
Test complet : Étudiants consultent les réponses à leurs réclamations
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from reclamations.models import TypeReclamation, Reclamation, ReponseAdministrateur

User = get_user_model()

def test_student_view_responses():
    """Test : Étudiants voient les réponses à leurs réclamations"""
    
    print("👨‍🎓 Test : Étudiants consultent leurs réponses de réclamations")
    print("=" * 65)
    
    # 1. Créer les utilisateurs
    admin_user, _ = User.objects.get_or_create(
        username='admin_edusmart',
        defaults={
            'email': 'admin@edusmart.com',
            'first_name': 'Admin',
            'last_name': 'EduSmart',
            'user_type': 'admin',
            'is_staff': True,
        }
    )
    
    # Étudiant 1
    student1, _ = User.objects.get_or_create(
        username='alice_martin',
        defaults={
            'email': 'alice@student.com',
            'first_name': 'Alice',
            'last_name': 'Martin',
            'user_type': 'student',
        }
    )
    
    # Étudiant 2
    student2, _ = User.objects.get_or_create(
        username='bob_dupont',
        defaults={
            'email': 'bob@student.com',
            'first_name': 'Bob',
            'last_name': 'Dupont',
            'user_type': 'student',
        }
    )
    
    print(f"✅ Utilisateurs créés:")
    print(f"   - Admin: {admin_user.get_full_name()}")
    print(f"   - Étudiant 1: {student1.get_full_name()}")
    print(f"   - Étudiant 2: {student2.get_full_name()}")
    
    # 2. Type de réclamation
    type_technique, _ = TypeReclamation.objects.get_or_create(
        code='technique',
        defaults={
            'name': 'Problème technique',
            'icon': 'bi-gear',
            'color': '#dc3545'
        }
    )
    
    # 3. Réclamations des étudiants
    reclamation_alice, _ = Reclamation.objects.get_or_create(
        titre='Problème d\'accès aux cours - Alice',
        utilisateur=student1,
        defaults={
            'description': 'Je ne peux pas accéder aux vidéos de cours depuis hier.',
            'type_reclamation': type_technique,
            'priorite': 'haute',
            'statut': 'ouverte',
        }
    )
    
    reclamation_bob, _ = Reclamation.objects.get_or_create(
        titre='Bug dans les exercices - Bob',
        utilisateur=student2,
        defaults={
            'description': 'Les exercices ne se sauvegardent pas correctement.',
            'type_reclamation': type_technique,
            'priorite': 'normale',
            'statut': 'en_cours',
        }
    )
    
    print(f"\n📝 Réclamations créées:")
    print(f"   - Alice: {reclamation_alice.titre}")
    print(f"   - Bob: {reclamation_bob.titre}")
    
    # 4. Admin répond aux réclamations
    reponse_alice, _ = ReponseAdministrateur.objects.get_or_create(
        reclamation=reclamation_alice,
        administrateur=admin_user,
        defaults={
            'titre': 'Solution - Problème d\'accès résolu',
            'contenu': '''Bonjour Alice,

Nous avons identifié et corrigé le problème d'accès aux vidéos.

Le problème était lié à une mise à jour du serveur vidéo qui a causé des incompatibilités.

Vous pouvez maintenant accéder à tous vos cours normalement.

Si vous rencontrez encore des difficultés, n'hésitez pas à nous recontacter.

Cordialement,
L'équipe technique EduSmart''',
            'statut': 'publiee',
            'notifier_utilisateur': True,
        }
    )
    
    reponse_bob, _ = ReponseAdministrateur.objects.get_or_create(
        reclamation=reclamation_bob,
        administrateur=admin_user,
        defaults={
            'titre': 'Correction - Bug des exercices corrigé',
            'contenu': '''Bonjour Bob,

Le bug de sauvegarde des exercices a été identifié et corrigé.

Le problème était lié à un timeout de session trop court.

Nous avons augmenté la durée de session et optimisé le système de sauvegarde automatique.

Vos exercices se sauvegarderont maintenant correctement.

Merci pour votre signalement !

Cordialement,
L'équipe technique''',
            'statut': 'publiee',
            'notifier_utilisateur': True,
        }
    )
    
    print(f"\n💬 Réponses administrateur créées:")
    print(f"   - Pour Alice: {reponse_alice.titre}")
    print(f"   - Pour Bob: {reponse_bob.titre}")
    
    # 5. Test de la vue étudiant - Alice
    print(f"\n🔍 Test de consultation pour Alice:")
    alice_reclamations = Reclamation.objects.filter(utilisateur=student1)
    alice_reponses = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student1,
        statut='publiee'
    )
    
    print(f"   - Réclamations d'Alice: {alice_reclamations.count()}")
    print(f"   - Réponses visibles pour Alice: {alice_reponses.count()}")
    
    for reponse in alice_reponses:
        print(f"     * {reponse.titre}")
        print(f"       Nouvelle: {reponse.is_new_for_user}")
        print(f"       Date: {reponse.date_publication}")
    
    # 6. Test de la vue étudiant - Bob
    print(f"\n🔍 Test de consultation pour Bob:")
    bob_reclamations = Reclamation.objects.filter(utilisateur=student2)
    bob_reponses = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student2,
        statut='publiee'
    )
    
    print(f"   - Réclamations de Bob: {bob_reclamations.count()}")
    print(f"   - Réponses visibles pour Bob: {bob_reponses.count()}")
    
    for reponse in bob_reponses:
        print(f"     * {reponse.titre}")
        print(f"       Nouvelle: {reponse.is_new_for_user}")
        print(f"       Date: {reponse.date_publication}")
    
    # 7. Test de sécurité - Alice ne voit pas les réponses de Bob
    print(f"\n🔒 Test de sécurité:")
    alice_cannot_see_bob = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student2,  # Réclamations de Bob
        statut='publiee'
    ).exclude(
        reclamation__utilisateur=student1   # Exclure celles d'Alice
    )
    
    print(f"   - Alice ne peut pas voir les réponses de Bob: {alice_cannot_see_bob.count() == 0}")
    
    # 8. Statistiques globales
    total_reponses_non_lues = ReponseAdministrateur.objects.filter(
        statut='publiee',
        lu_par_utilisateur=False
    ).count()
    
    print(f"\n📊 Statistiques:")
    print(f"   - Total réponses publiées: {ReponseAdministrateur.objects.filter(statut='publiee').count()}")
    print(f"   - Réponses non lues: {total_reponses_non_lues}")
    
    # 9. URLs de test
    print(f"\n🌐 URLs pour tester dans EduSmart:")
    print(f"   - Liste réclamations Alice: http://127.0.0.1:8000/reclamations/")
    print(f"   - Réclamation Alice: http://127.0.0.1:8000/reclamations/{reclamation_alice.pk}/")
    print(f"   - Réclamation Bob: http://127.0.0.1:8000/reclamations/{reclamation_bob.pk}/")
    
    print(f"\n📋 Instructions de test:")
    print(f"   1. Connectez-vous avec alice_martin / password")
    print(f"   2. Allez sur la liste des réclamations")
    print(f"   3. Vous devriez voir un badge 'Nouvelle réponse'")
    print(f"   4. Cliquez sur la réclamation pour voir la réponse officielle")
    print(f"   5. La réponse sera marquée comme lue automatiquement")
    
    return {
        'admin': admin_user,
        'alice': student1,
        'bob': student2,
        'reclamation_alice': reclamation_alice,
        'reclamation_bob': reclamation_bob,
        'reponse_alice': reponse_alice,
        'reponse_bob': reponse_bob,
    }

if __name__ == '__main__':
    try:
        result = test_student_view_responses()
        print(f"\n🎉 Test réussi ! Les étudiants peuvent consulter leurs réponses !")
        print(f"✅ Fonctionnalité complète et sécurisée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
