#!/usr/bin/env python
"""
Debug : Vérifier tous les utilisateurs et leurs réponses
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from reclamations.models import TypeReclamation, Reclamation, ReponseAdministrateur

User = get_user_model()

def debug_all_users_responses():
    """Debug de tous les utilisateurs et leurs réponses"""
    
    print("🔍 Debug : Tous les utilisateurs et leurs réponses")
    print("=" * 60)
    
    # 1. Lister tous les utilisateurs
    all_users = User.objects.all()
    print(f"👥 Total utilisateurs: {all_users.count()}")
    
    for user in all_users:
        print(f"   - {user.username} ({user.get_full_name()}) - Type: {user.user_type}")
    
    # 2. Lister toutes les réclamations
    all_reclamations = Reclamation.objects.all()
    print(f"\n📝 Total réclamations: {all_reclamations.count()}")
    
    for reclamation in all_reclamations:
        print(f"   - ID {reclamation.pk}: {reclamation.titre}")
        print(f"     Utilisateur: {reclamation.utilisateur.username}")
        print(f"     Statut: {reclamation.get_statut_display()}")
    
    # 3. Lister toutes les réponses administrateur
    all_reponses = ReponseAdministrateur.objects.all()
    print(f"\n💬 Total réponses admin: {all_reponses.count()}")
    
    for reponse in all_reponses:
        print(f"   - ID {reponse.pk}: {reponse.titre}")
        print(f"     Réclamation: {reponse.reclamation.titre} (ID: {reponse.reclamation.pk})")
        print(f"     Utilisateur concerné: {reponse.reclamation.utilisateur.username}")
        print(f"     Admin: {reponse.administrateur.username}")
        print(f"     Statut: {reponse.get_statut_display()}")
        print(f"     Lu par utilisateur: {reponse.lu_par_utilisateur}")
        print(f"     Date création: {reponse.created_at}")
        if reponse.date_lecture:
            print(f"     Date lecture: {reponse.date_lecture}")
        print()
    
    # 4. Vérifier les réponses non lues par utilisateur
    print(f"🔔 Réponses non lues par utilisateur:")
    
    users_with_reclamations = User.objects.filter(reclamation__isnull=False).distinct()
    
    for user in users_with_reclamations:
        reponses_non_lues = ReponseAdministrateur.objects.filter(
            reclamation__utilisateur=user,
            statut='publiee',
            lu_par_utilisateur=False
        )
        
        print(f"   - {user.username}: {reponses_non_lues.count()} réponse(s) non lue(s)")
        
        for reponse in reponses_non_lues:
            print(f"     * {reponse.titre} (Réclamation: {reponse.reclamation.titre})")
    
    # 5. Chercher spécifiquement des utilisateurs avec 'moamen' dans le nom
    moamen_users = User.objects.filter(username__icontains='moamen')
    print(f"\n🔍 Utilisateurs contenant 'moamen': {moamen_users.count()}")
    
    for user in moamen_users:
        print(f"   - {user.username} ({user.get_full_name()})")
        
        # Vérifier ses réclamations
        user_reclamations = Reclamation.objects.filter(utilisateur=user)
        print(f"     Réclamations: {user_reclamations.count()}")
        
        # Vérifier ses réponses non lues
        user_reponses_non_lues = ReponseAdministrateur.objects.filter(
            reclamation__utilisateur=user,
            statut='publiee',
            lu_par_utilisateur=False
        )
        print(f"     Réponses non lues: {user_reponses_non_lues.count()}")
        
        if user_reponses_non_lues.exists():
            for reponse in user_reponses_non_lues:
                print(f"       * {reponse.titre}")
    
    # 6. Créer une réponse de test si nécessaire
    if all_reclamations.exists() and all_users.filter(is_staff=True).exists():
        admin_user = all_users.filter(is_staff=True).first()
        test_reclamation = all_reclamations.first()
        
        print(f"\n🧪 Création d'une réponse de test:")
        print(f"   Admin: {admin_user.username}")
        print(f"   Réclamation: {test_reclamation.titre} (Utilisateur: {test_reclamation.utilisateur.username})")
        
        # Créer ou mettre à jour une réponse de test
        reponse_test, created = ReponseAdministrateur.objects.get_or_create(
            reclamation=test_reclamation,
            titre="DEBUG - Réponse de test non lue",
            defaults={
                'administrateur': admin_user,
                'contenu': 'Ceci est une réponse de test pour débugger les réponses non lues.',
                'statut': 'publiee',
                'lu_par_utilisateur': False,
            }
        )
        
        if created:
            print(f"   ✅ Nouvelle réponse créée: {reponse_test.titre}")
        else:
            # Réinitialiser comme non lue
            reponse_test.lu_par_utilisateur = False
            reponse_test.date_lecture = None
            reponse_test.save()
            print(f"   🔄 Réponse existante réinitialisée: {reponse_test.titre}")
        
        # Vérifier le résultat
        final_count = ReponseAdministrateur.objects.filter(
            reclamation__utilisateur=test_reclamation.utilisateur,
            statut='publiee',
            lu_par_utilisateur=False
        ).count()
        
        print(f"   📊 Réponses non lues pour {test_reclamation.utilisateur.username}: {final_count}")
        
        if final_count > 0:
            print(f"   🌐 Testez avec l'utilisateur: {test_reclamation.utilisateur.username}")
            print(f"   🔗 URL: http://127.0.0.1:8000/reclamations/")

if __name__ == '__main__':
    try:
        debug_all_users_responses()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
