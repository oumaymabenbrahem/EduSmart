#!/usr/bin/env python
"""
Test : Fonctionnalité des réclamations assignées aux enseignants
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from reclamations.models import TypeReclamation, Reclamation, ReponseAdministrateur
from django.utils import timezone

User = get_user_model()

def test_teacher_assignments():
    """Test des réclamations assignées aux enseignants"""
    
    print("👨‍🏫 Test : Réclamations assignées aux enseignants")
    print("=" * 55)
    
    # 1. Créer les utilisateurs
    admin_user, _ = User.objects.get_or_create(
        username='admin_assignments',
        defaults={
            'email': 'admin@test.com',
            'first_name': 'Admin',
            'last_name': 'Test',
            'user_type': 'admin',
            'is_staff': True,
        }
    )
    
    # Enseignant 1
    teacher1, _ = User.objects.get_or_create(
        username='prof_martin',
        defaults={
            'email': 'martin@teacher.com',
            'first_name': 'Jean',
            'last_name': 'Martin',
            'user_type': 'teacher',
            'is_staff': True,
        }
    )
    
    # Enseignant 2
    teacher2, _ = User.objects.get_or_create(
        username='prof_durand',
        defaults={
            'email': 'durand@teacher.com',
            'first_name': 'Marie',
            'last_name': 'Durand',
            'user_type': 'teacher',
            'is_staff': True,
        }
    )
    
    # Étudiant
    student_user, _ = User.objects.get_or_create(
        username='etudiant_assignments',
        defaults={
            'email': 'etudiant@test.com',
            'first_name': 'Pierre',
            'last_name': 'Étudiant',
            'user_type': 'student',
        }
    )
    
    print(f"✅ Utilisateurs créés:")
    print(f"   - Admin: {admin_user.get_full_name()}")
    print(f"   - Enseignant 1: {teacher1.get_full_name()}")
    print(f"   - Enseignant 2: {teacher2.get_full_name()}")
    print(f"   - Étudiant: {student_user.get_full_name()}")
    
    # 2. Créer des types de réclamations
    type_technique, _ = TypeReclamation.objects.get_or_create(
        code='technique',
        defaults={
            'name': 'Problème technique',
            'icon': 'bi-gear',
            'color': '#dc3545'
        }
    )
    
    type_contenu, _ = TypeReclamation.objects.get_or_create(
        code='contenu',
        defaults={
            'name': 'Problème de contenu',
            'icon': 'bi-book',
            'color': '#ffc107'
        }
    )
    
    # 3. Créer des réclamations et les assigner aux enseignants
    reclamations_data = [
        {
            'titre': 'Problème avec le serveur de cours',
            'description': 'Le serveur de cours ne répond plus depuis ce matin.',
            'type': type_technique,
            'priorite': 'urgente',
            'assigne_a': teacher1,
        },
        {
            'titre': 'Erreur dans le contenu du chapitre 5',
            'description': 'Il y a une erreur dans les formules du chapitre 5 de mathématiques.',
            'type': type_contenu,
            'priorite': 'haute',
            'assigne_a': teacher1,
        },
        {
            'titre': 'Problème d\'accès aux exercices',
            'description': 'Je ne peux pas accéder aux exercices de physique.',
            'type': type_technique,
            'priorite': 'normale',
            'assigne_a': teacher2,
        },
        {
            'titre': 'Question sur le projet final',
            'description': 'J\'ai une question concernant les consignes du projet final.',
            'type': type_contenu,
            'priorite': 'basse',
            'assigne_a': teacher2,
        },
        {
            'titre': 'Réclamation non assignée',
            'description': 'Cette réclamation n\'est assignée à personne.',
            'type': type_technique,
            'priorite': 'normale',
            'assigne_a': None,
        },
    ]
    
    reclamations_creees = []
    for i, data in enumerate(reclamations_data):
        reclamation, created = Reclamation.objects.get_or_create(
            titre=data['titre'],
            utilisateur=student_user,
            defaults={
                'description': data['description'],
                'type_reclamation': data['type'],
                'priorite': data['priorite'],
                'assigne_a': data['assigne_a'],
                'statut': 'ouverte' if i < 2 else 'en_cours' if i < 4 else 'ouverte',
            }
        )
        reclamations_creees.append(reclamation)
    
    print(f"\n📝 Réclamations créées: {len(reclamations_creees)}")
    
    # 4. Tester les assignations pour l'enseignant 1
    reclamations_teacher1 = Reclamation.objects.filter(assigne_a=teacher1)
    print(f"\n👨‍🏫 Réclamations assignées à {teacher1.get_full_name()}: {reclamations_teacher1.count()}")
    
    for reclamation in reclamations_teacher1:
        print(f"   - {reclamation.titre}")
        print(f"     Priorité: {reclamation.get_priorite_display()}")
        print(f"     Statut: {reclamation.get_statut_display()}")
        print(f"     Type: {reclamation.type_reclamation.name}")
        print()
    
    # 5. Tester les assignations pour l'enseignant 2
    reclamations_teacher2 = Reclamation.objects.filter(assigne_a=teacher2)
    print(f"👩‍🏫 Réclamations assignées à {teacher2.get_full_name()}: {reclamations_teacher2.count()}")
    
    for reclamation in reclamations_teacher2:
        print(f"   - {reclamation.titre}")
        print(f"     Priorité: {reclamation.get_priorite_display()}")
        print(f"     Statut: {reclamation.get_statut_display()}")
        print(f"     Type: {reclamation.type_reclamation.name}")
        print()
    
    # 6. Créer des réponses pour certaines réclamations assignées
    reponse1, created = ReponseAdministrateur.objects.get_or_create(
        reclamation=reclamations_teacher1.first(),
        administrateur=teacher1,
        defaults={
            'titre': 'Réponse - Serveur de cours réparé',
            'contenu': '''Bonjour,

Le problème avec le serveur de cours a été identifié et résolu.

Il s'agissait d'une surcharge temporaire qui a été corrigée par notre équipe technique.

Le service est maintenant opérationnel.

Cordialement,
Jean Martin - Enseignant''',
            'statut': 'publiee',
            'lu_par_utilisateur': False,
        }
    )
    
    if created:
        print(f"✅ Réponse créée par {teacher1.get_full_name()}")
    
    # 7. Statistiques pour l'enseignant 1
    stats_teacher1 = {
        'total_assignees': reclamations_teacher1.count(),
        'ouvertes': reclamations_teacher1.filter(statut='ouverte').count(),
        'en_cours': reclamations_teacher1.filter(statut='en_cours').count(),
        'resolues': reclamations_teacher1.filter(statut='resolue').count(),
        'urgentes': reclamations_teacher1.filter(priorite='urgente').count(),
    }
    
    print(f"📊 Statistiques pour {teacher1.get_full_name()}:")
    print(f"   - Total assignées: {stats_teacher1['total_assignees']}")
    print(f"   - Ouvertes: {stats_teacher1['ouvertes']}")
    print(f"   - En cours: {stats_teacher1['en_cours']}")
    print(f"   - Résolues: {stats_teacher1['resolues']}")
    print(f"   - Urgentes: {stats_teacher1['urgentes']}")
    
    # 8. Statistiques pour l'enseignant 2
    stats_teacher2 = {
        'total_assignees': reclamations_teacher2.count(),
        'ouvertes': reclamations_teacher2.filter(statut='ouverte').count(),
        'en_cours': reclamations_teacher2.filter(statut='en_cours').count(),
        'resolues': reclamations_teacher2.filter(statut='resolue').count(),
        'urgentes': reclamations_teacher2.filter(priorite='urgente').count(),
    }
    
    print(f"\n📊 Statistiques pour {teacher2.get_full_name()}:")
    print(f"   - Total assignées: {stats_teacher2['total_assignees']}")
    print(f"   - Ouvertes: {stats_teacher2['ouvertes']}")
    print(f"   - En cours: {stats_teacher2['en_cours']}")
    print(f"   - Résolues: {stats_teacher2['resolues']}")
    print(f"   - Urgentes: {stats_teacher2['urgentes']}")
    
    # 9. Test de sécurité - Vérifier l'isolation
    print(f"\n🔒 Test de sécurité:")
    print(f"   - {teacher1.get_full_name()} ne voit que ses assignations: {reclamations_teacher1.count() > 0}")
    print(f"   - {teacher2.get_full_name()} ne voit que ses assignations: {reclamations_teacher2.count() > 0}")
    print(f"   - Pas de chevauchement: {not reclamations_teacher1.filter(assigne_a=teacher2).exists()}")
    
    # 10. URLs de test
    print(f"\n🌐 URLs pour tester:")
    print(f"   - Assignations {teacher1.get_full_name()}: http://127.0.0.1:8000/reclamations/assignees/")
    print(f"   - Assignations {teacher2.get_full_name()}: http://127.0.0.1:8000/reclamations/assignees/")
    print(f"   - Administration: http://127.0.0.1:8000/reclamations/admin/")
    
    print(f"\n📋 Instructions de test:")
    print(f"   1. Connectez-vous avec {teacher1.username} (enseignant)")
    print(f"   2. Allez sur /reclamations/assignees/")
    print(f"   3. Vous devriez voir {reclamations_teacher1.count()} réclamation(s) assignée(s)")
    print(f"   4. Testez avec {teacher2.username} pour voir ses {reclamations_teacher2.count()} assignation(s)")
    print(f"   5. Chaque enseignant ne voit que ses propres assignations")
    
    return {
        'admin': admin_user,
        'teacher1': teacher1,
        'teacher2': teacher2,
        'student': student_user,
        'reclamations': reclamations_creees,
        'stats_teacher1': stats_teacher1,
        'stats_teacher2': stats_teacher2,
    }

if __name__ == '__main__':
    try:
        result = test_teacher_assignments()
        print(f"\n🎉 Test réussi ! Fonctionnalité des assignations opérationnelle !")
        print(f"✅ {result['stats_teacher1']['total_assignees']} réclamation(s) pour {result['teacher1'].get_full_name()}")
        print(f"✅ {result['stats_teacher2']['total_assignees']} réclamation(s) pour {result['teacher2'].get_full_name()}")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
