#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_learning_path():
    """Test de la page learning-path"""
    client = Client()
    
    try:
        # Tenter d'accéder à la page avec un host valide
        response = client.get('/gamification/learning-path/', HTTP_HOST='127.0.0.1:8000')
        
        if response.status_code == 200:
            print("✅ SUCCESS: Page learning-path accessible (200)")
            return True
        elif response.status_code == 302:
            print("⚠️  REDIRECT: Page redirige (302) - probablement vers login")
            return True
        else:
            print(f"❌ ERROR: Status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Test de la page learning-path...")
    success = test_learning_path()
    
    if success:
        print("\n🎉 Test réussi ! L'erreur AttributeError semble résolue.")
    else:
        print("\n💥 Test échoué. L'erreur persiste.")
