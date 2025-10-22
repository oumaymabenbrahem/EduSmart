#!/usr/bin/env python
"""
Script pour créer un superutilisateur automatiquement
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Créer le superutilisateur s'il n'existe pas
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@edusmart.com',
        password='admin123',
        first_name='Admin',
        last_name='EduSmart',
        user_type='admin'
    )
    print("Superutilisateur créé avec succès!")
    print("Username: admin")
    print("Password: admin123")
    print("Email: admin@edusmart.com")
else:
    print("Le superutilisateur existe déjà.")

# Créer quelques utilisateurs de test
test_users = [
    {
        'username': 'student1',
        'email': 'student1@edusmart.com',
        'password': 'student123',
        'first_name': 'Marie',
        'last_name': 'Dupont',
        'user_type': 'student'
    },
    {
        'username': 'teacher1',
        'email': 'teacher1@edusmart.com',
        'password': 'teacher123',
        'first_name': 'Jean',
        'last_name': 'Martin',
        'user_type': 'teacher'
    }
]

for user_data in test_users:
    if not User.objects.filter(username=user_data['username']).exists():
        User.objects.create_user(**user_data)
        print(f"Utilisateur de test créé: {user_data['username']}")

print("\nConfiguration terminée!")
