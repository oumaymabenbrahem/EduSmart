#!/usr/bin/env python
"""
Script pour réinitialiser complètement la base de données
"""
import os
import shutil
import subprocess
import sys

def run_command(command):
    """Exécuter une commande et afficher le résultat"""
    print(f"Exécution: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Erreur: {result.stderr}")
    return result.returncode == 0

def main():
    # Supprimer la base de données
    if os.path.exists('db.sqlite3'):
        try:
            os.remove('db.sqlite3')
            print("Base de données supprimée")
        except:
            print("Impossible de supprimer la base de données (peut-être en cours d'utilisation)")
    
    # Supprimer les migrations existantes
    migrations_dirs = [
        'accounts/migrations',
        'template_front/migrations', 
        'template_back/migrations'
    ]
    
    for migrations_dir in migrations_dirs:
        if os.path.exists(migrations_dir):
            for file in os.listdir(migrations_dir):
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(migrations_dir, file)
                    try:
                        os.remove(file_path)
                        print(f"Migration supprimée: {file_path}")
                    except:
                        print(f"Impossible de supprimer: {file_path}")
    
    # Créer les nouvelles migrations
    print("\n=== Création des migrations ===")
    if not run_command("python manage.py makemigrations accounts"):
        print("Erreur lors de la création des migrations accounts")
        return False
    
    if not run_command("python manage.py makemigrations"):
        print("Erreur lors de la création des autres migrations")
        return False
    
    # Appliquer les migrations
    print("\n=== Application des migrations ===")
    if not run_command("python manage.py migrate"):
        print("Erreur lors de l'application des migrations")
        return False
    
    print("\n=== Base de données réinitialisée avec succès! ===")
    return True

if __name__ == '__main__':
    main()
