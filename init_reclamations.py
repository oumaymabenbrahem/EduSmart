# -*- coding: utf-8 -*-
"""
Script d'initialisation des types de réclamations par défaut
Usage: python init_reclamations.py
"""

import os
import sys
import django

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from reclamations.models import TypeReclamation


def create_default_types():
    """Créer les types de réclamations par défaut"""
    
    types_data = [
        {
            'name': 'Problème technique',
            'code': 'technique',
            'description': 'Bugs, erreurs système, problèmes de performance, dysfonctionnements',
            'icon': 'bi-bug',
            'color': '#dc3545'
        },
        {
            'name': 'Problème de contenu',
            'code': 'contenu',
            'description': 'Contenu incorrect, manquant, obsolète ou inapproprié',
            'icon': 'bi-file-text',
            'color': '#fd7e14'
        },
        {
            'name': 'Problème d\'accès',
            'code': 'acces',
            'description': 'Difficultés de connexion, permissions, authentification',
            'icon': 'bi-key',
            'color': '#6f42c1'
        },
        {
            'name': 'Problème d\'évaluation',
            'code': 'evaluation',
            'description': 'Questions d\'examen, notation, résultats incorrects',
            'icon': 'bi-clipboard-check',
            'color': '#0dcaf0'
        },
        {
            'name': 'Problème de forum',
            'code': 'forum',
            'description': 'Messages, modération, interactions dans le forum',
            'icon': 'bi-chat-dots',
            'color': '#198754'
        },
        {
            'name': 'Autre',
            'code': 'autre',
            'description': 'Autres problèmes non classifiés dans les catégories précédentes',
            'icon': 'bi-question-circle',
            'color': '#6c757d'
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for type_data in types_data:
        type_obj, created = TypeReclamation.objects.get_or_create(
            code=type_data['code'],
            defaults=type_data
        )
        
        if created:
            created_count += 1
            print(f"[OK] Cree: {type_obj.name}")
        else:
            # Mettre à jour si nécessaire
            updated = False
            for field, value in type_data.items():
                if field != 'code' and getattr(type_obj, field) != value:
                    setattr(type_obj, field, value)
                    updated = True
            
            if updated:
                type_obj.save()
                updated_count += 1
                print(f"[MAJ] Mis a jour: {type_obj.name}")
            else:
                print(f"[INFO] Existe deja: {type_obj.name}")
    
    print(f"\nResume:")
    print(f"   - Types crees: {created_count}")
    print(f"   - Types mis a jour: {updated_count}")
    print(f"   - Total des types: {TypeReclamation.objects.count()}")


if __name__ == '__main__':
    print("Initialisation des types de reclamations...")
    create_default_types()
    print("Initialisation terminee!")
