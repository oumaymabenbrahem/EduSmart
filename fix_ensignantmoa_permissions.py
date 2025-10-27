#!/usr/bin/env python
"""
Corriger les permissions de l'enseignant ensignantmoa
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def fix_ensignantmoa_permissions():
    """Corriger les permissions d'ensignantmoa"""
    
    print("🔧 Correction des permissions pour ensignantmoa")
    print("=" * 50)
    
    try:
        ensignant_moa = User.objects.get(username='ensignantmoa')
        
        print(f"👨‍🏫 Utilisateur: {ensignant_moa.username}")
        print(f"   - Nom: {ensignant_moa.get_full_name()}")
        print(f"   - Type: {ensignant_moa.user_type}")
        print(f"   - Staff (avant): {ensignant_moa.is_staff}")
        print(f"   - Superuser (avant): {ensignant_moa.is_superuser}")
        
        # Corriger les permissions
        ensignant_moa.is_staff = True  # Nécessaire pour accéder aux fonctions admin
        ensignant_moa.save()
        
        print(f"\n✅ Permissions corrigées:")
        print(f"   - Staff (après): {ensignant_moa.is_staff}")
        print(f"   - Type utilisateur: {ensignant_moa.user_type}")
        
        # Vérifier les réclamations assignées
        from reclamations.models import Reclamation
        reclamations_assignees = Reclamation.objects.filter(assigne_a=ensignant_moa)
        
        print(f"\n📋 Réclamations assignées: {reclamations_assignees.count()}")
        for reclamation in reclamations_assignees:
            print(f"   - {reclamation.titre} ({reclamation.get_priorite_display()})")
        
        print(f"\n🌐 Maintenant ensignantmoa peut:")
        print(f"   ✅ Se connecter à EduSmart")
        print(f"   ✅ Voir le menu 'Réclamations' dans la navigation")
        print(f"   ✅ Accéder à 'Mes Assignations'")
        print(f"   ✅ Répondre aux réclamations assignées")
        print(f"   ✅ Accéder aux fonctions d'administration")
        
        print(f"\n📋 Instructions de test:")
        print(f"   1. Allez sur: http://127.0.0.1:8000/")
        print(f"   2. Connectez-vous avec: ensignantmoa")
        print(f"   3. Cliquez sur 'Réclamations' dans la navigation")
        print(f"   4. Sélectionnez 'Mes Assignations'")
        print(f"   5. Vous devriez voir {reclamations_assignees.count()} réclamations")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Utilisateur 'ensignantmoa' non trouvé")
        return False

if __name__ == '__main__':
    try:
        success = fix_ensignantmoa_permissions()
        if success:
            print(f"\n🎉 Permissions corrigées avec succès !")
            print(f"✅ ensignantmoa peut maintenant accéder à toutes ses fonctionnalités")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
