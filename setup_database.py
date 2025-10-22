#!/usr/bin/env python
"""
Script pour configurer la base de données avec le modèle User personnalisé
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
    django.setup()
    
    # Supprimer la base de données si elle existe
    db_path = 'db.sqlite3'
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Base de données {db_path} supprimée.")
        except OSError as e:
            print(f"Erreur lors de la suppression de {db_path}: {e}")
    
    # Créer les migrations
    print("Création des migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # Appliquer les migrations
    print("Application des migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("Base de données configurée avec succès!")
    
    # Créer un superutilisateur
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        print("Création du superutilisateur...")
        User.objects.create_superuser(
            username='admin',
            email='admin@edusmart.com',
            password='admin123',
            first_name='Admin',
            last_name='EduSmart',
            user_type='admin'
        )
        print("Superutilisateur créé: admin / admin123")
    
    print("Configuration terminée!")
