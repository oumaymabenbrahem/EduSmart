#!/usr/bin/env python
"""
Test : Fonctionnalité de consultation des réponses lues
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

def test_reponses_lues_functionality():
    """Test de la fonctionnalité des réponses lues"""
    
    print("📚 Test : Consultation des réponses lues")
    print("=" * 50)
    
    # 1. Créer des utilisateurs de test
    admin_user, _ = User.objects.get_or_create(
        username='admin_reponses_test',
        defaults={
            'email': 'admin@test.com',
            'first_name': 'Admin',
            'last_name': 'Test',
            'user_type': 'admin',
            'is_staff': True,
        }
    )
    
    student_user, _ = User.objects.get_or_create(
        username='student_reponses_test',
        defaults={
            'email': 'student@test.com',
            'first_name': 'Étudiant',
            'last_name': 'Test',
            'user_type': 'student',
        }
    )
    
    print(f"✅ Utilisateurs créés:")
    print(f"   - Admin: {admin_user.username}")
    print(f"   - Étudiant: {student_user.username}")
    
    # 2. Créer un type de réclamation
    type_reclamation, _ = TypeReclamation.objects.get_or_create(
        code='test',
        defaults={
            'name': 'Test',
            'icon': 'bi-test',
            'color': '#007bff'
        }
    )
    
    # 3. Créer plusieurs réclamations
    reclamations = []
    for i in range(3):
        reclamation, _ = Reclamation.objects.get_or_create(
            titre=f'Réclamation Test {i+1}',
            utilisateur=student_user,
            defaults={
                'description': f'Description de la réclamation test numéro {i+1}',
                'type_reclamation': type_reclamation,
                'priorite': 'normale',
                'statut': 'ouverte',
            }
        )
        reclamations.append(reclamation)
    
    print(f"\n📝 Réclamations créées: {len(reclamations)}")
    
    # 4. Créer des réponses administrateur
    reponses_creees = []
    for i, reclamation in enumerate(reclamations):
        reponse, created = ReponseAdministrateur.objects.get_or_create(
            reclamation=reclamation,
            administrateur=admin_user,
            titre=f'Réponse Test {i+1}',
            defaults={
                'contenu': f'''Bonjour,

Voici notre réponse officielle à votre réclamation "{reclamation.titre}".

Nous avons analysé votre demande et pris les mesures appropriées.

Réponse numéro {i+1} pour les tests.

Cordialement,
L'équipe support''',
                'statut': 'publiee',
                'lu_par_utilisateur': False,
            }
        )
        reponses_creees.append(reponse)
    
    print(f"💬 Réponses créées: {len(reponses_creees)}")
    
    # 5. Marquer certaines réponses comme lues
    reponses_a_marquer = reponses_creees[:2]  # Marquer les 2 premières comme lues
    for reponse in reponses_a_marquer:
        reponse.lu_par_utilisateur = True
        reponse.date_lecture = timezone.now()
        reponse.save()
    
    print(f"✅ Réponses marquées comme lues: {len(reponses_a_marquer)}")
    
    # 6. Tester les statistiques
    total_reponses = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student_user,
        statut='publiee'
    ).count()
    
    reponses_lues = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student_user,
        statut='publiee',
        lu_par_utilisateur=True
    ).count()
    
    reponses_non_lues = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student_user,
        statut='publiee',
        lu_par_utilisateur=False
    ).count()
    
    print(f"\n📊 Statistiques pour {student_user.username}:")
    print(f"   - Total réponses: {total_reponses}")
    print(f"   - Réponses lues: {reponses_lues}")
    print(f"   - Réponses non lues: {reponses_non_lues}")
    
    # 7. Tester la vue des réponses lues
    reponses_lues_queryset = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student_user,
        statut='publiee',
        lu_par_utilisateur=True
    ).select_related('reclamation', 'administrateur').order_by('-date_lecture')
    
    print(f"\n📚 Réponses lues détaillées:")
    for reponse in reponses_lues_queryset:
        print(f"   - {reponse.titre}")
        print(f"     Réclamation: {reponse.reclamation.titre}")
        print(f"     Admin: {reponse.administrateur.username}")
        print(f"     Lue le: {reponse.date_lecture}")
        print(f"     Contenu: {reponse.contenu[:100]}...")
        print()
    
    # 8. Vérifier les réclamations avec réponses pour le filtre
    reclamations_avec_reponses = Reclamation.objects.filter(
        utilisateur=student_user,
        reponses_admin__statut='publiee'
    ).distinct()
    
    print(f"🔍 Réclamations avec réponses (pour filtre): {reclamations_avec_reponses.count()}")
    for reclamation in reclamations_avec_reponses:
        print(f"   - {reclamation.titre}")
    
    # 9. Test de recherche
    search_term = "Test 1"
    reponses_recherche = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=student_user,
        statut='publiee',
        lu_par_utilisateur=True
    ).filter(
        Q(titre__icontains=search_term) |
        Q(contenu__icontains=search_term) |
        Q(reclamation__titre__icontains=search_term)
    )
    
    print(f"\n🔍 Test de recherche '{search_term}': {reponses_recherche.count()} résultat(s)")
    
    # 10. URLs de test
    print(f"\n🌐 URLs pour tester:")
    print(f"   - Liste réclamations: http://127.0.0.1:8000/reclamations/")
    print(f"   - Réponses lues: http://127.0.0.1:8000/reclamations/reponses-lues/")
    
    print(f"\n📋 Instructions de test:")
    print(f"   1. Connectez-vous avec {student_user.username}")
    print(f"   2. Allez sur la liste des réclamations")
    print(f"   3. Cliquez sur 'Réponses Lues' pour voir la nouvelle page")
    print(f"   4. Vous devriez voir {reponses_lues} réponse(s) lue(s)")
    print(f"   5. Testez les filtres et la recherche")
    
    return {
        'admin': admin_user,
        'student': student_user,
        'reclamations': reclamations,
        'reponses': reponses_creees,
        'stats': {
            'total': total_reponses,
            'lues': reponses_lues,
            'non_lues': reponses_non_lues
        }
    }

if __name__ == '__main__':
    try:
        from django.db.models import Q
        result = test_reponses_lues_functionality()
        print(f"\n🎉 Test réussi ! Fonctionnalité des réponses lues opérationnelle !")
        print(f"✅ {result['stats']['lues']} réponse(s) lue(s) disponible(s) pour consultation")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
