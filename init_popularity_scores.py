"""
Script rapide pour initialiser les scores de popularité
Usage: python init_popularity_scores.py
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from forum.ai_popularity_predictor import TopicPopularityPredictor
from forum.models import Topic
from django.utils import timezone
from datetime import timedelta

def main():
    print("🔄 Initialisation des scores de popularité...")
    
    # Charger le prédicteur
    predictor = TopicPopularityPredictor()
    
    # Récupérer les topics récents (30 derniers jours)
    cutoff = timezone.now() - timedelta(days=30)
    topics = Topic.objects.filter(
        is_active=True,
        created_at__gte=cutoff
    ).select_related('author', 'category')
    
    total = topics.count()
    print(f"📊 {total} topics à traiter")
    
    if total == 0:
        print("⚠ Aucun topic à traiter")
        return
    
    # Mettre à jour chaque topic
    updated = 0
    for i, topic in enumerate(topics, 1):
        try:
            score = predictor.update_topic_popularity(topic)
            updated += 1
            
            if i % 10 == 0:
                print(f"  ⏳ {i}/{total} - Score du topic '{topic.title[:50]}': {score:.2f}")
        
        except Exception as e:
            print(f"  ⚠ Erreur topic {topic.id}: {e}")
    
    print(f"\n✅ Terminé ! {updated}/{total} topics mis à jour")
    print("\n💡 Pour entraîner un modèle ML, utilisez:")
    print("   python manage.py train_popularity_model")
    print("\n💡 Pour mettre à jour régulièrement les scores:")
    print("   python manage.py update_popularity_scores")

if __name__ == '__main__':
    main()
