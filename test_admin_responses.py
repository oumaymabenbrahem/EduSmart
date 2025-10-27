#!/usr/bin/env python
"""
Script de test pour les réponses administrateur aux réclamations
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from reclamations.models import TypeReclamation, Reclamation, ReponseAdministrateur
from django.utils import timezone

User = get_user_model()

def test_admin_responses():
    """Test de la fonctionnalité des réponses administrateur"""
    
    print("🔍 Test des réponses administrateur aux réclamations")
    print("=" * 60)
    
    # 1. Créer ou récupérer un utilisateur admin
    admin_user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@edusmart.com',
            'first_name': 'Admin',
            'last_name': 'Test',
            'user_type': 'admin',
            'is_staff': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✅ Utilisateur admin créé: {admin_user.username}")
    else:
        print(f"✅ Utilisateur admin trouvé: {admin_user.username}")
    
    # 2. Créer ou récupérer un utilisateur étudiant
    student_user, created = User.objects.get_or_create(
        username='student_test',
        defaults={
            'email': 'student@edusmart.com',
            'first_name': 'Étudiant',
            'last_name': 'Test',
            'user_type': 'student',
        }
    )
    if created:
        student_user.set_password('student123')
        student_user.save()
        print(f"✅ Utilisateur étudiant créé: {student_user.username}")
    else:
        print(f"✅ Utilisateur étudiant trouvé: {student_user.username}")
    
    # 3. Créer ou récupérer un type de réclamation
    type_reclamation, created = TypeReclamation.objects.get_or_create(
        code='technique',
        defaults={
            'name': 'Problème technique',
            'description': 'Problèmes liés à la plateforme',
            'icon': 'bi-gear',
            'color': '#dc3545',
        }
    )
    if created:
        print(f"✅ Type de réclamation créé: {type_reclamation.name}")
    else:
        print(f"✅ Type de réclamation trouvé: {type_reclamation.name}")
    
    # 4. Créer une réclamation de test
    reclamation, created = Reclamation.objects.get_or_create(
        titre='Test - Problème de connexion',
        utilisateur=student_user,
        defaults={
            'description': 'Je n\'arrive pas à me connecter à la plateforme depuis ce matin.',
            'type_reclamation': type_reclamation,
            'priorite': 'normale',
            'statut': 'ouverte',
        }
    )
    if created:
        print(f"✅ Réclamation créée: {reclamation.titre}")
    else:
        print(f"✅ Réclamation trouvée: {reclamation.titre}")
    
    # 5. Créer une réponse administrateur
    reponse, created = ReponseAdministrateur.objects.get_or_create(
        reclamation=reclamation,
        administrateur=admin_user,
        defaults={
            'titre': 'Réponse officielle - Problème de connexion résolu',
            'contenu': '''Bonjour,

Nous avons identifié et résolu le problème de connexion que vous avez signalé.

Le problème était lié à une maintenance serveur qui a eu lieu ce matin entre 8h et 10h.

Vous devriez maintenant pouvoir vous connecter normalement. Si le problème persiste, n'hésitez pas à nous recontacter.

Cordialement,
L'équipe technique EduSmart''',
            'statut': 'publiee',
            'notifier_utilisateur': True,
        }
    )
    if created:
        print(f"✅ Réponse administrateur créée: {reponse.titre}")
    else:
        print(f"✅ Réponse administrateur trouvée: {reponse.titre}")
    
    # 6. Vérifier les propriétés de la réponse
    print(f"\n📊 Détails de la réponse:")
    print(f"   - ID: {reponse.id}")
    print(f"   - Titre: {reponse.titre}")
    print(f"   - Statut: {reponse.get_statut_display()}")
    print(f"   - Publiée: {reponse.is_published}")
    print(f"   - Nouvelle pour l'utilisateur: {reponse.is_new_for_user}")
    print(f"   - Date de création: {reponse.created_at}")
    if reponse.date_publication:
        print(f"   - Date de publication: {reponse.date_publication}")
    
    # 7. Tester les relations
    print(f"\n🔗 Relations:")
    print(f"   - Réclamation liée: {reponse.reclamation.titre}")
    print(f"   - Administrateur: {reponse.administrateur.get_full_name()}")
    print(f"   - Utilisateur de la réclamation: {reclamation.utilisateur.get_full_name()}")
    
    # 8. Compter les réponses pour cette réclamation
    total_reponses = reclamation.reponses_admin.count()
    reponses_publiees = reclamation.reponses_admin.filter(statut='publiee').count()
    print(f"\n📈 Statistiques:")
    print(f"   - Total des réponses: {total_reponses}")
    print(f"   - Réponses publiées: {reponses_publiees}")
    
    # 9. Tester la vue utilisateur (réponses visibles)
    reponses_visibles = reclamation.reponses_admin.filter(statut='publiee')
    print(f"   - Réponses visibles par l'utilisateur: {reponses_visibles.count()}")
    
    print(f"\n✅ Test terminé avec succès!")
    print(f"🌐 Vous pouvez maintenant tester l'interface web:")
    print(f"   - Réclamation: http://127.0.0.1:8000/reclamations/{reclamation.pk}/")
    print(f"   - Admin: http://127.0.0.1:8000/admin/reclamations/reclamation/{reclamation.pk}/change/")
    
    return {
        'admin_user': admin_user,
        'student_user': student_user,
        'reclamation': reclamation,
        'reponse': reponse,
    }

if __name__ == '__main__':
    try:
        result = test_admin_responses()
        print(f"\n🎉 Tous les tests sont passés!")
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
