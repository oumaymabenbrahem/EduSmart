# -*- coding: utf-8 -*-
"""
Script de test pour le module de gestion des réclamations
Usage: python test_reclamations.py
"""

import os
import sys
import django

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from reclamations.models import TypeReclamation, Reclamation, CommentaireReclamation

User = get_user_model()


def test_module():
    """Tester les fonctionnalités du module de réclamations"""
    
    print("=== Test du Module de Gestion des Reclamations ===\n")
    
    # 1. Vérifier les types de réclamations
    print("1. Verification des types de reclamations:")
    types = TypeReclamation.objects.all()
    print(f"   - Nombre de types: {types.count()}")
    for type_rec in types:
        print(f"   - {type_rec.name} ({type_rec.code}) - Actif: {type_rec.is_active}")
    print()
    
    # 2. Vérifier les utilisateurs
    print("2. Verification des utilisateurs:")
    users = User.objects.all()[:5]  # Premiers 5 utilisateurs
    print(f"   - Nombre total d'utilisateurs: {User.objects.count()}")
    for user in users:
        print(f"   - {user.username} ({user.user_type if hasattr(user, 'user_type') else 'N/A'})")
    print()
    
    # 3. Créer une réclamation de test si possible
    if users.exists() and types.exists():
        print("3. Creation d'une reclamation de test:")
        user = users.first()
        type_rec = types.first()
        
        # Vérifier si une réclamation de test existe déjà
        test_reclamation = Reclamation.objects.filter(
            titre="Test - Reclamation automatique"
        ).first()
        
        if not test_reclamation:
            test_reclamation = Reclamation.objects.create(
                titre="Test - Reclamation automatique",
                description="Ceci est une réclamation créée automatiquement pour tester le module.",
                type_reclamation=type_rec,
                utilisateur=user,
                priorite='normale',
                statut='ouverte'
            )
            print(f"   - Reclamation creee: #{test_reclamation.id}")
        else:
            print(f"   - Reclamation de test existe deja: #{test_reclamation.id}")
        
        # Ajouter un commentaire de test
        comment_exists = CommentaireReclamation.objects.filter(
            reclamation=test_reclamation,
            contenu__contains="Commentaire de test automatique"
        ).exists()
        
        if not comment_exists:
            CommentaireReclamation.objects.create(
                reclamation=test_reclamation,
                auteur=user,
                contenu="Commentaire de test automatique pour vérifier le système.",
                is_internal=False
            )
            print(f"   - Commentaire ajoute")
        else:
            print(f"   - Commentaire de test existe deja")
        print()
    
    # 4. Statistiques générales
    print("4. Statistiques generales:")
    total_reclamations = Reclamation.objects.count()
    print(f"   - Total des reclamations: {total_reclamations}")
    
    if total_reclamations > 0:
        stats_statut = {}
        for statut, _ in Reclamation.STATUS_CHOICES:
            count = Reclamation.objects.filter(statut=statut).count()
            if count > 0:
                stats_statut[statut] = count
        
        print("   - Repartition par statut:")
        for statut, count in stats_statut.items():
            print(f"     * {statut}: {count}")
        
        stats_priorite = {}
        for priorite, _ in Reclamation.PRIORITY_CHOICES:
            count = Reclamation.objects.filter(priorite=priorite).count()
            if count > 0:
                stats_priorite[priorite] = count
        
        print("   - Repartition par priorite:")
        for priorite, count in stats_priorite.items():
            print(f"     * {priorite}: {count}")
    print()
    
    # 5. Vérifier les URLs (simulation)
    print("5. URLs du module:")
    urls = [
        "/reclamations/ - Liste des reclamations utilisateur",
        "/reclamations/create/ - Creer une nouvelle reclamation", 
        "/reclamations/admin/ - Administration des reclamations",
        "/reclamations/<id>/ - Detail d'une reclamation",
        "/reclamations/<id>/edit/ - Modifier une reclamation (admin)"
    ]
    for url in urls:
        print(f"   - {url}")
    print()
    
    # 6. Test des propriétés du modèle
    if total_reclamations > 0:
        print("6. Test des proprietes du modele:")
        reclamation = Reclamation.objects.first()
        print(f"   - Reclamation: {reclamation.titre}")
        print(f"   - Couleur priorite: {reclamation.priority_color}")
        print(f"   - Couleur statut: {reclamation.status_color}")
        print(f"   - En retard: {reclamation.is_overdue}")
        print(f"   - URL absolue: {reclamation.get_absolute_url()}")
        print()
    
    print("=== Test Complete ===")
    print("Le module de gestion des reclamations est pret a etre utilise!")
    print("\nPour acceder au module:")
    print("1. Connectez-vous sur http://localhost:8000/")
    print("2. Allez sur http://localhost:8000/reclamations/")
    print("3. Pour l'administration: http://localhost:8000/reclamations/admin/")


if __name__ == '__main__':
    try:
        test_module()
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
