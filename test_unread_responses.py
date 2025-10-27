#!/usr/bin/env python
"""
Test spécifique : Vérification des réponses non lues
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from reclamations.models import TypeReclamation, Reclamation, ReponseAdministrateur
from django.db.models import Exists, OuterRef

User = get_user_model()

def test_unread_responses():
    """Test spécifique pour les réponses non lues"""
    
    print("🔍 Test : Vérification des réponses non lues")
    print("=" * 50)
    
    # 1. Vérifier l'utilisateur Moamen2
    try:
        moamen_user = User.objects.get(username='Moamen2')
        print(f"✅ Utilisateur trouvé: {moamen_user.username}")
    except User.DoesNotExist:
        print("❌ Utilisateur 'Moamen2' non trouvé")
        return
    
    # 2. Vérifier ses réclamations
    reclamations_moamen = Reclamation.objects.filter(utilisateur=moamen_user)
    print(f"📝 Réclamations de {moamen_user.username}: {reclamations_moamen.count()}")
    
    for reclamation in reclamations_moamen:
        print(f"   - {reclamation.titre} (ID: {reclamation.pk})")
    
    # 3. Vérifier les réponses administrateur
    reponses_moamen = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=moamen_user
    )
    print(f"\n💬 Réponses pour {moamen_user.username}: {reponses_moamen.count()}")
    
    for reponse in reponses_moamen:
        print(f"   - {reponse.titre}")
        print(f"     Statut: {reponse.get_statut_display()}")
        print(f"     Lu par utilisateur: {reponse.lu_par_utilisateur}")
        print(f"     Date création: {reponse.created_at}")
        if reponse.date_lecture:
            print(f"     Date lecture: {reponse.date_lecture}")
        print()
    
    # 4. Vérifier les réponses non lues spécifiquement
    reponses_non_lues = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=moamen_user,
        statut='publiee',
        lu_par_utilisateur=False
    )
    print(f"🔔 Réponses NON LUES pour {moamen_user.username}: {reponses_non_lues.count()}")
    
    for reponse in reponses_non_lues:
        print(f"   - {reponse.titre} (ID: {reponse.pk})")
        print(f"     Réclamation: {reponse.reclamation.titre}")
        print(f"     Créée le: {reponse.created_at}")
    
    # 5. Test de la logique d'annotation
    print(f"\n🔍 Test de la logique d'annotation:")
    
    # Sous-requête pour vérifier s'il y a des réponses non lues
    reponses_non_lues_subquery = ReponseAdministrateur.objects.filter(
        reclamation=OuterRef('pk'),
        statut='publiee',
        lu_par_utilisateur=False
    )
    
    # Annoter les réclamations avec l'information des réponses non lues
    reclamations_annotated = reclamations_moamen.annotate(
        has_unread_responses=Exists(reponses_non_lues_subquery)
    )
    
    for reclamation in reclamations_annotated:
        print(f"   - {reclamation.titre}: has_unread_responses = {reclamation.has_unread_responses}")
    
    # 6. Statistiques globales
    total_reponses_non_lues = ReponseAdministrateur.objects.filter(
        reclamation__utilisateur=moamen_user,
        statut='publiee',
        lu_par_utilisateur=False
    ).count()
    
    print(f"\n📊 Statistiques pour {moamen_user.username}:")
    print(f"   - Total réclamations: {reclamations_moamen.count()}")
    print(f"   - Total réponses: {reponses_moamen.count()}")
    print(f"   - Réponses publiées: {reponses_moamen.filter(statut='publiee').count()}")
    print(f"   - Réponses non lues: {total_reponses_non_lues}")
    
    # 7. Créer une nouvelle réponse non lue pour test
    if reclamations_moamen.exists():
        admin_user = User.objects.filter(is_staff=True).first()
        if admin_user:
            reclamation_test = reclamations_moamen.first()
            
            # Vérifier s'il y a déjà une réponse de test
            reponse_test, created = ReponseAdministrateur.objects.get_or_create(
                reclamation=reclamation_test,
                administrateur=admin_user,
                titre="Test - Réponse non lue",
                defaults={
                    'contenu': 'Ceci est une réponse de test pour vérifier les réponses non lues.',
                    'statut': 'publiee',
                    'lu_par_utilisateur': False,
                }
            )
            
            if created:
                print(f"\n✅ Réponse de test créée: {reponse_test.titre}")
            else:
                # S'assurer qu'elle n'est pas marquée comme lue
                if reponse_test.lu_par_utilisateur:
                    reponse_test.lu_par_utilisateur = False
                    reponse_test.date_lecture = None
                    reponse_test.save()
                    print(f"\n🔄 Réponse de test réinitialisée: {reponse_test.titre}")
                else:
                    print(f"\n✅ Réponse de test existante: {reponse_test.titre}")
            
            # Revérifier les statistiques
            total_reponses_non_lues_apres = ReponseAdministrateur.objects.filter(
                reclamation__utilisateur=moamen_user,
                statut='publiee',
                lu_par_utilisateur=False
            ).count()
            
            print(f"\n📊 Après création/réinitialisation:")
            print(f"   - Réponses non lues: {total_reponses_non_lues_apres}")
            
            if total_reponses_non_lues_apres > 0:
                print(f"✅ Le problème devrait être résolu !")
                print(f"🌐 Testez maintenant: http://127.0.0.1:8000/reclamations/")
            else:
                print(f"❌ Problème persistant - aucune réponse non lue détectée")

if __name__ == '__main__':
    try:
        test_unread_responses()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
