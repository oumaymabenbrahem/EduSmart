#!/usr/bin/env python
"""
Assigner des réclamations à l'enseignant ensignantmoa
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

def assign_reclamations_to_ensignantmoa():
    """Assigner des réclamations à ensignantmoa"""
    
    print("👨‍🏫 Assignation de réclamations à ensignantmoa")
    print("=" * 50)
    
    # 1. Vérifier si l'utilisateur ensignantmoa existe
    try:
        ensignant_moa = User.objects.get(username='ensignantmoa')
        print(f"✅ Enseignant trouvé: {ensignant_moa.username}")
        print(f"   - Nom complet: {ensignant_moa.get_full_name()}")
        print(f"   - Type: {ensignant_moa.user_type}")
        print(f"   - Staff: {ensignant_moa.is_staff}")
    except User.DoesNotExist:
        print("❌ Utilisateur 'ensignantmoa' non trouvé")
        return
    
    # 2. Vérifier les réclamations actuellement assignées
    reclamations_assignees = Reclamation.objects.filter(assigne_a=ensignant_moa)
    print(f"\n📋 Réclamations actuellement assignées: {reclamations_assignees.count()}")
    
    for reclamation in reclamations_assignees:
        print(f"   - {reclamation.titre} (ID: {reclamation.pk})")
    
    # 3. Trouver des réclamations non assignées
    reclamations_non_assignees = Reclamation.objects.filter(assigne_a__isnull=True)
    print(f"\n📝 Réclamations non assignées disponibles: {reclamations_non_assignees.count()}")
    
    for reclamation in reclamations_non_assignees[:5]:  # Afficher les 5 premières
        print(f"   - {reclamation.titre} (ID: {reclamation.pk}) - {reclamation.get_statut_display()}")
    
    # 4. Créer des réclamations de test si nécessaire
    if reclamations_non_assignees.count() == 0:
        print(f"\n🔧 Création de réclamations de test...")
        
        # Créer un type de réclamation si nécessaire
        type_technique, _ = TypeReclamation.objects.get_or_create(
            code='technique',
            defaults={
                'name': 'Problème technique',
                'icon': 'bi-gear',
                'color': '#dc3545'
            }
        )
        
        # Créer un utilisateur étudiant pour les réclamations
        etudiant_test, _ = User.objects.get_or_create(
            username='etudiant_pour_moa',
            defaults={
                'email': 'etudiant@test.com',
                'first_name': 'Étudiant',
                'last_name': 'Test',
                'user_type': 'student',
            }
        )
        
        # Créer des réclamations de test
        reclamations_test = [
            {
                'titre': 'Problème serveur cours en ligne',
                'description': 'Le serveur des cours en ligne ne répond plus depuis ce matin. Les étudiants ne peuvent pas accéder aux contenus.',
                'priorite': 'urgente',
                'statut': 'ouverte',
            },
            {
                'titre': 'Bug interface évaluation',
                'description': 'L\'interface d\'évaluation affiche des erreurs lors de la soumission des réponses.',
                'priorite': 'haute',
                'statut': 'ouverte',
            },
            {
                'titre': 'Problème accès forum étudiant',
                'description': 'Un étudiant signale qu\'il ne peut pas accéder au forum de discussion de son cours.',
                'priorite': 'normale',
                'statut': 'en_cours',
            },
            {
                'titre': 'Erreur téléchargement documents',
                'description': 'Les documents de cours ne se téléchargent pas correctement.',
                'priorite': 'haute',
                'statut': 'ouverte',
            },
        ]
        
        nouvelles_reclamations = []
        for i, data in enumerate(reclamations_test):
            reclamation, created = Reclamation.objects.get_or_create(
                titre=data['titre'],
                utilisateur=etudiant_test,
                defaults={
                    'description': data['description'],
                    'type_reclamation': type_technique,
                    'priorite': data['priorite'],
                    'statut': data['statut'],
                }
            )
            if created:
                nouvelles_reclamations.append(reclamation)
        
        print(f"✅ {len(nouvelles_reclamations)} nouvelles réclamations créées")
        reclamations_non_assignees = Reclamation.objects.filter(assigne_a__isnull=True)
    
    # 5. Assigner des réclamations à ensignantmoa
    reclamations_a_assigner = reclamations_non_assignees[:4]  # Prendre les 4 premières
    
    print(f"\n🎯 Assignation de {reclamations_a_assigner.count()} réclamations à {ensignant_moa.username}:")
    
    for reclamation in reclamations_a_assigner:
        reclamation.assigne_a = ensignant_moa
        reclamation.save()
        print(f"   ✅ Assigné: {reclamation.titre}")
        print(f"      Priorité: {reclamation.get_priorite_display()}")
        print(f"      Statut: {reclamation.get_statut_display()}")
        print(f"      Utilisateur: {reclamation.utilisateur.get_full_name()}")
        print()
    
    # 6. Créer une réponse de test pour une réclamation
    if reclamations_a_assigner.exists():
        premiere_reclamation = reclamations_a_assigner.first()
        
        reponse_test, created = ReponseAdministrateur.objects.get_or_create(
            reclamation=premiere_reclamation,
            administrateur=ensignant_moa,
            defaults={
                'titre': f'Réponse - {premiere_reclamation.titre}',
                'contenu': f'''Bonjour,

J'ai pris en charge votre réclamation concernant "{premiere_reclamation.titre}".

Après analyse, j'ai identifié la cause du problème et mis en place les corrections nécessaires.

Le problème devrait maintenant être résolu. 

Si vous rencontrez encore des difficultés, n'hésitez pas à me recontacter.

Cordialement,
{ensignant_moa.get_full_name() or ensignant_moa.username}
Enseignant EduSmart''',
                'statut': 'publiee',
                'lu_par_utilisateur': False,
            }
        )
        
        if created:
            print(f"💬 Réponse créée pour: {premiere_reclamation.titre}")
    
    # 7. Vérification finale
    reclamations_finales = Reclamation.objects.filter(assigne_a=ensignant_moa)
    
    print(f"\n📊 Résultat final pour {ensignant_moa.username}:")
    print(f"   - Total assignées: {reclamations_finales.count()}")
    print(f"   - Ouvertes: {reclamations_finales.filter(statut='ouverte').count()}")
    print(f"   - En cours: {reclamations_finales.filter(statut='en_cours').count()}")
    print(f"   - Urgentes: {reclamations_finales.filter(priorite='urgente').count()}")
    print(f"   - Hautes: {reclamations_finales.filter(priorite='haute').count()}")
    
    # 8. URLs de test
    print(f"\n🌐 URLs pour tester:")
    print(f"   - Assignations: http://127.0.0.1:8000/reclamations/assignees/")
    print(f"   - Administration: http://127.0.0.1:8000/reclamations/admin/")
    
    print(f"\n📋 Instructions:")
    print(f"   1. Connectez-vous avec le compte 'ensignantmoa'")
    print(f"   2. Allez sur EduSmart: http://127.0.0.1:8000/")
    print(f"   3. Cliquez sur 'Réclamations' dans la navigation")
    print(f"   4. Sélectionnez 'Mes Assignations'")
    print(f"   5. Vous devriez voir {reclamations_finales.count()} réclamation(s) assignée(s)")
    
    return {
        'enseignant': ensignant_moa,
        'reclamations_assignees': reclamations_finales,
        'count': reclamations_finales.count()
    }

if __name__ == '__main__':
    try:
        result = assign_reclamations_to_ensignantmoa()
        print(f"\n🎉 Assignation réussie !")
        print(f"✅ {result['count']} réclamation(s) assignée(s) à {result['enseignant'].username}")
        print(f"✅ L'enseignant peut maintenant voir ses assignations dans EduSmart")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
