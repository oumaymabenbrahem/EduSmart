""" # main.py
from recommender import load_dataset, clean_dataset, train_model, recommend_courses

# 1️⃣ Charger le dataset
df = load_dataset()

# 2️⃣ Nettoyer les données
df = clean_dataset(df)

# 3️⃣ Entraîner le modèle
train_model(df)

# 4️⃣ Tester une recommandation
test_course = "AWS Fundamentals"
print(f"\n🎯 Recommandations pour : {test_course}\n")

recommendations = recommend_courses(test_course, df)
# Par exemple, ne prendre que le titre
for i, rec in enumerate(recommendations, 1):
    title = rec[0]   # 0 = course_title
    print(f"{i}. {title}")
"""
# main.py
import sys
import os
import django

# Ajouter la racine du projet
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

# Définir le settings Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EduSmart.settings")

# Initialiser Django
django.setup()

from django.contrib.auth import get_user_model
from cours.ai.recommender import train_model, recommend_for_student

# Entraîner le modèle
train_model()

# Étudiant de test
User = get_user_model()
try:
    student = User.objects.get(username='yosr')
except User.DoesNotExist:
    print("❌ Utilisateur non trouvé")
    exit()


# Générer les recommandations
recommendations = recommend_for_student(student)

print(f"\n🎯 Recommandations pour {student.username} :\n")
if not recommendations:
    print("❌ Aucune recommandation disponible pour le moment.")
else:
    for i, rec in enumerate(recommendations, 1):
        # rec doit être un tuple (title, rating)
        if isinstance(rec, (list, tuple)) and len(rec) == 2:
            title, rating = rec
            print(f"{i}. {title} | Rating: {rating}")

