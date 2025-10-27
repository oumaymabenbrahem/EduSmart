"""
Script de test rapide pour le système de prédiction de popularité
Usage: python test_prediction_system.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from forum.ai_popularity_predictor import get_predictor, predict_topic_popularity
from forum.models import Topic, Category
from accounts.models import CustomUser


def test_prediction_system():
    """Test complet du système de prédiction"""
    
    print("=" * 60)
    print("🧪 TEST DU SYSTÈME DE PRÉDICTION DE POPULARITÉ")
    print("=" * 60)
    
    # 1. Vérifier les dépendances
    print("\n1️⃣ Vérification des dépendances...")
    try:
        import numpy
        import pandas
        import sklearn
        print("   ✅ numpy:", numpy.__version__)
        print("   ✅ pandas:", pandas.__version__)
        print("   ✅ scikit-learn:", sklearn.__version__)
    except ImportError as e:
        print(f"   ❌ Dépendance manquante: {e}")
        print("   💡 Installez avec: pip install -r requirements_ml.txt")
        return False
    
    # 2. Vérifier le prédicteur
    print("\n2️⃣ Initialisation du prédicteur...")
    try:
        predictor = get_predictor()
        print("   ✅ Prédicteur initialisé")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # 3. Vérifier les données
    print("\n3️⃣ Vérification des données...")
    topic_count = Topic.objects.filter(is_active=True).count()
    category_count = Category.objects.filter(is_active=True).count()
    user_count = CustomUser.objects.count()
    
    print(f"   📊 Topics: {topic_count}")
    print(f"   📁 Catégories: {category_count}")
    print(f"   👥 Utilisateurs: {user_count}")
    
    if topic_count < 10:
        print("   ⚠️  Peu de données. Créez plus de topics pour de meilleures prédictions.")
    
    # 4. Test de prédiction basique
    print("\n4️⃣ Test de prédiction...")
    
    if category_count == 0:
        print("   ❌ Aucune catégorie. Créez des catégories d'abord.")
        return False
    
    if user_count == 0:
        print("   ❌ Aucun utilisateur. Créez un utilisateur d'abord.")
        return False
    
    # Prendre la première catégorie et le premier utilisateur
    test_category = Category.objects.filter(is_active=True).first()
    test_user = CustomUser.objects.first()
    
    try:
        prediction = predict_topic_popularity(
            title="Comment utiliser Django pour créer un forum ?",
            content="""Je suis débutant en Django et je voudrais créer un forum.
            Quelles sont les étapes à suivre ? Avez-vous des ressources ?
            
            Voici ce que j'ai déjà essayé :
            ```python
            from django.db import models
            
            class Topic(models.Model):
                title = models.CharField(max_length=200)
            ```
            
            Merci d'avance !""",
            category_id=test_category.id,
            author_id=test_user.id
        )
        
        print("   ✅ Prédiction réussie!")
        print(f"\n   📊 Résultats:")
        print(f"   • Vues prévues: {prediction['predicted_views']}")
        print(f"   • Posts prévus: {prediction['predicted_posts']}")
        print(f"   • Score: {prediction['popularity_score']}/100")
        print(f"   • Catégorie: {prediction['category']}")
        print(f"   • Confiance: {prediction['confidence']}")
        print(f"   • Méthode: {prediction['method']}")
        
        if prediction['recommendations']:
            print(f"\n   💡 Recommandations:")
            for rec in prediction['recommendations']:
                print(f"      - {rec}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la prédiction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. État du modèle
    print("\n5️⃣ État du modèle ML...")
    if predictor.model_views and predictor.model_posts:
        print("   ✅ Modèles ML entraînés et chargés")
        print("   💡 Les prédictions utilisent le Machine Learning")
    else:
        print("   ⚠️  Modèles ML non entraînés")
        print("   💡 Les prédictions utilisent des heuristiques")
        print(f"\n   📝 Pour entraîner les modèles:")
        print(f"      python manage.py train_popularity_models")
        print(f"\n   Nécessite au moins {topic_count}/50 topics")
    
    # 6. Test d'analyse si des topics existent
    if topic_count > 0:
        print("\n6️⃣ Test d'analyse de performance...")
        test_topic = Topic.objects.filter(is_active=True).first()
        
        try:
            analysis = predictor.analyze_topic_performance(test_topic.id)
            
            if 'error' not in analysis:
                print(f"   ✅ Analyse réussie pour: '{test_topic.title}'")
                print(f"\n   📈 Performance:")
                print(f"   • Vues prévues: {analysis['predicted_views']}")
                print(f"   • Vues réelles: {analysis['actual_views']}")
                print(f"   • Différence: {analysis['views_difference']:+d}")
                print(f"   • Performance: {analysis['performance']}")
            else:
                print(f"   ❌ {analysis['error']}")
                
        except Exception as e:
            print(f"   ❌ Erreur lors de l'analyse: {e}")
    
    # 7. Résumé
    print("\n" + "=" * 60)
    print("✅ SYSTÈME FONCTIONNEL")
    print("=" * 60)
    
    print("\n📋 Prochaines étapes:")
    
    if topic_count < 50:
        print(f"   1. Créer plus de topics (actuellement: {topic_count}/50)")
        print("      → Manuellement ou avec: python manage.py create_demo_topics")
    
    if not predictor.model_views:
        print("   2. Entraîner les modèles ML")
        print("      → python manage.py train_popularity_models")
    
    print("   3. Tester dans l'interface web")
    print("      → Créer un nouveau topic et voir la prédiction")
    
    print("   4. Consulter les statistiques")
    print("      → http://localhost:8000/forum/admin/popularity-stats/")
    
    print("\n💡 Guide complet: GUIDE_PREDICTION_POPULARITE.md")
    
    return True


if __name__ == "__main__":
    try:
        success = test_prediction_system()
        if success:
            print("\n🎉 Tous les tests sont passés!")
        else:
            print("\n⚠️  Certains tests ont échoué. Voir les messages ci-dessus.")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
