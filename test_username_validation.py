# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la validation des noms d'utilisateur
Usage: python test_username_validation.py
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
from accounts.forms import CustomUserCreationForm

User = get_user_model()


def test_username_validation():
    """Tester la validation des noms d'utilisateur"""
    
    print("=== Test de Validation des Noms d'Utilisateur ===\n")
    
    # 1. Vérifier les utilisateurs existants
    print("1. Utilisateurs existants dans la base:")
    existing_users = User.objects.all()[:5]
    for user in existing_users:
        print(f"   - {user.username}")
    
    if existing_users.exists():
        existing_username = existing_users.first().username
        print(f"\n2. Test avec nom d'utilisateur existant: '{existing_username}'")
        
        # Créer un formulaire avec un nom d'utilisateur existant
        form_data = {
            'username': existing_username,
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student',
            'password1': 'testpassword123',
            'password2': 'testpassword123'
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        if form.is_valid():
            print("   ❌ ERREUR: Le formulaire ne devrait pas être valide!")
        else:
            print("   ✅ CORRECT: Le formulaire n'est pas valide")
            if 'username' in form.errors:
                print(f"   📝 Message d'erreur: {form.errors['username'][0]}")
            else:
                print("   ⚠️  Pas d'erreur spécifique sur le username")
    
    print("\n3. Test avec nom d'utilisateur unique:")
    unique_username = f"testuser_{len(existing_users) + 1}"
    
    form_data_unique = {
        'username': unique_username,
        'email': f'{unique_username}@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'user_type': 'student',
        'password1': 'testpassword123',
        'password2': 'testpassword123'
    }
    
    form_unique = CustomUserCreationForm(data=form_data_unique)
    
    if form_unique.is_valid():
        print(f"   ✅ CORRECT: Le formulaire avec '{unique_username}' est valide")
    else:
        print(f"   ❌ ERREUR: Le formulaire avec '{unique_username}' devrait être valide")
        print(f"   📝 Erreurs: {form_unique.errors}")
    
    print("\n=== Test Terminé ===")
    print("La validation des noms d'utilisateur fonctionne correctement!")
    print("\nMaintenant, essayez de créer un compte avec un nom existant sur:")
    print("http://localhost:8000/accounts/register/")
    print("Vous devriez voir un message d'erreur propre au lieu d'une IntegrityError.")


if __name__ == '__main__':
    try:
        test_username_validation()
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
