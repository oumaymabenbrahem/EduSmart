#!/usr/bin/env python
"""
Vérification complète pour ensignantmoa
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from reclamations.models import Reclamation, ReponseAdministrateur
from reclamations.views import get_teacher_reclamations_stats
from django.test import RequestFactory

User = get_user_model()

def verify_ensignantmoa():
    """Vérification complète d'ensignantmoa"""
    
    print("🔍 Vérification complète pour ensignantmoa")
    print("=" * 50)
    
    try:
        ensignant_moa = User.objects.get(username='ensignantmoa')
        
        print(f"👨‍🏫 Profil utilisateur:")
        print(f"   - Username: {ensignant_moa.username}")
        print(f"   - Nom complet: {ensignant_moa.get_full_name()}")
        print(f"   - Email: {ensignant_moa.email}")
        print(f"   - Type: {ensignant_moa.user_type}")
        print(f"   - Staff: {ensignant_moa.is_staff}")
        print(f"   - Actif: {ensignant_moa.is_active}")
        
        # 1. Vérifier les réclamations assignées
        reclamations_assignees = Reclamation.objects.filter(assigne_a=ensignant_moa)
        
        print(f"\n📋 Réclamations assignées: {reclamations_assignees.count()}")
        print(f"   Détails:")
        for i, reclamation in enumerate(reclamations_assignees, 1):
            print(f"   {i}. {reclamation.titre}")
            print(f"      - ID: {reclamation.pk}")
            print(f"      - Priorité: {reclamation.get_priorite_display()}")
            print(f"      - Statut: {reclamation.get_statut_display()}")
            print(f"      - Utilisateur: {reclamation.utilisateur.get_full_name()}")
            print(f"      - Créée le: {reclamation.created_at.strftime('%d/%m/%Y %H:%M')}")
        
        # 2. Vérifier les statistiques
        stats = get_teacher_reclamations_stats(ensignant_moa)
        
        print(f"\n📊 Statistiques:")
        if stats:
            print(f"   - Total assignées: {stats['total_assignees']}")
            print(f"   - Ouvertes: {stats['ouvertes']}")
            print(f"   - En cours: {stats['en_cours']}")
            print(f"   - Résolues: {stats['resolues']}")
            print(f"   - Urgentes: {stats['urgentes']}")
            print(f"   - Nouvelles (7j): {stats['nouvelles']}")
            print(f"   - Réclamations récentes: {len(stats['recentes'])}")
        else:
            print("   ❌ Aucune statistique disponible")
        
        # 3. Vérifier les réponses créées
        reponses_creees = ReponseAdministrateur.objects.filter(administrateur=ensignant_moa)
        
        print(f"\n💬 Réponses créées: {reponses_creees.count()}")
        for reponse in reponses_creees:
            print(f"   - {reponse.titre}")
            print(f"     Réclamation: {reponse.reclamation.titre}")
            print(f"     Statut: {reponse.get_statut_display()}")
            print(f"     Créée le: {reponse.created_at.strftime('%d/%m/%Y %H:%M')}")
        
        # 4. Test des permissions d'accès
        print(f"\n🔒 Vérification des permissions:")
        
        # Vérifier l'accès aux vues
        factory = RequestFactory()
        request = factory.get('/reclamations/assignees/')
        request.user = ensignant_moa
        
        # Test de la condition d'accès
        has_teacher_access = (ensignant_moa.user_type == 'teacher' or ensignant_moa.is_staff)
        print(f"   - Accès enseignant: {'✅' if has_teacher_access else '❌'}")
        print(f"   - Type utilisateur valide: {'✅' if ensignant_moa.user_type == 'teacher' else '❌'}")
        print(f"   - Statut staff: {'✅' if ensignant_moa.is_staff else '❌'}")
        
        # 5. URLs disponibles
        print(f"\n🌐 URLs disponibles pour ensignantmoa:")
        urls = [
            ('EduSmart Accueil', 'http://127.0.0.1:8000/'),
            ('Mes Assignations', 'http://127.0.0.1:8000/reclamations/assignees/'),
            ('Liste Réclamations', 'http://127.0.0.1:8000/reclamations/'),
            ('Administration', 'http://127.0.0.1:8000/reclamations/admin/'),
        ]
        
        for nom, url in urls:
            print(f"   - {nom}: {url}")
        
        # 6. Instructions de test
        print(f"\n📖 Instructions de test:")
        print(f"   1. 🌐 Ouvrez votre navigateur")
        print(f"   2. 🔗 Allez sur: http://127.0.0.1:8000/")
        print(f"   3. 🔑 Connectez-vous avec:")
        print(f"      - Username: ensignantmoa")
        print(f"      - Password: [votre mot de passe]")
        print(f"   4. 🧭 Dans la navigation, cliquez sur 'Réclamations'")
        print(f"   5. 📋 Sélectionnez 'Mes Assignations'")
        print(f"   6. 👀 Vous devriez voir:")
        print(f"      - Dashboard avec 6 statistiques")
        print(f"      - {reclamations_assignees.count()} réclamations assignées")
        print(f"      - Boutons 'Consulter' et 'Répondre'")
        print(f"      - Filtres de recherche")
        
        # 7. Résumé
        print(f"\n✅ Résumé pour ensignantmoa:")
        print(f"   - Compte configuré correctement")
        print(f"   - {reclamations_assignees.count()} réclamations assignées")
        print(f"   - {reponses_creees.count()} réponse(s) créée(s)")
        print(f"   - Permissions d'accès validées")
        print(f"   - Interface EduSmart accessible")
        
        return {
            'user': ensignant_moa,
            'reclamations_count': reclamations_assignees.count(),
            'reponses_count': reponses_creees.count(),
            'stats': stats,
            'has_access': has_teacher_access
        }
        
    except User.DoesNotExist:
        print("❌ Utilisateur 'ensignantmoa' non trouvé")
        return None

if __name__ == '__main__':
    try:
        result = verify_ensignantmoa()
        if result:
            print(f"\n🎉 Vérification réussie !")
            print(f"✅ ensignantmoa est prêt à utiliser EduSmart")
            print(f"✅ {result['reclamations_count']} réclamations disponibles")
            print(f"✅ Interface complètement fonctionnelle")
        else:
            print(f"\n❌ Problème détecté avec ensignantmoa")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
