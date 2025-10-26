"""
Script pour vérifier et afficher les topics populaires
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from forum.models import Topic, Category
from forum.ai_popularity_predictor import TopicPopularityPredictor, get_popular_topics
from django.db.models import Count

def main():
    print("=" * 80)
    print("🔍 ANALYSE DES TOPICS POPULAIRES")
    print("=" * 80)
    
    # Catégorie Annonces
    try:
        annonces = Category.objects.get(slug='annonces')
        print(f"\n📁 Catégorie: {annonces.name}")
        print("-" * 80)
        
        # Tous les topics
        topics = Topic.objects.filter(
            is_active=True,
            category=annonces
        ).annotate(
            posts_count=Count('posts')
        ).order_by('-popularity_score')
        
        print(f"\n📊 Total topics dans Annonces: {topics.count()}")
        
        if topics.count() == 0:
            print("⚠ Aucun topic dans cette catégorie")
            return
        
        print(f"\n🔥 Top 5 topics par score de popularité:")
        print("-" * 80)
        
        for i, topic in enumerate(topics[:5], 1):
            print(f"\n{i}. {topic.title}")
            print(f"   Score: {topic.popularity_score:.2f}")
            print(f"   Vues: {topic.views}")
            print(f"   Réponses: {topic.posts_count}")
            print(f"   Auteur: {topic.author.username}")
            print(f"   Créé le: {topic.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Vérifier le seuil
        print("\n" + "=" * 80)
        print("🎯 ANALYSE DU SEUIL DE POPULARITÉ")
        print("=" * 80)
        
        predictor = TopicPopularityPredictor()
        
        # Topics des 48 dernières heures
        popular = get_popular_topics(category=annonces, limit=5, hours=48)
        print(f"\n📅 Topics des 48 dernières heures: {popular.count()}")
        
        if popular.count() == 0:
            print("\n⚠ Aucun topic dans les 48 dernières heures")
            print("💡 Essayons avec une période plus longue (7 jours)...")
            
            popular = get_popular_topics(category=annonces, limit=5, hours=168)
            print(f"\n📅 Topics des 7 derniers jours: {popular.count()}")
        
        if popular.count() > 0:
            print(f"\n✅ Topics qui seraient affichés:")
            for topic in popular:
                print(f"   - {topic.title} (score: {topic.popularity_score:.2f})")
        else:
            print("\n❌ Aucun topic ne dépasse le seuil de popularité")
            print("\n💡 SOLUTIONS:")
            print("   1. Augmenter l'activité sur les topics (vues, réponses)")
            print("   2. Modifier le seuil de temps (actuellement 48h)")
            print("   3. Recalculer les scores avec: python init_popularity_scores.py")
        
        # Statistiques globales
        print("\n" + "=" * 80)
        print("📈 STATISTIQUES GLOBALES")
        print("=" * 80)
        
        avg_score = sum(t.popularity_score for t in topics) / topics.count()
        max_score = max(t.popularity_score for t in topics)
        min_score = min(t.popularity_score for t in topics)
        
        print(f"\n   Score moyen: {avg_score:.2f}")
        print(f"   Score maximum: {max_score:.2f}")
        print(f"   Score minimum: {min_score:.2f}")
        
        topics_with_score = topics.filter(popularity_score__gt=0).count()
        print(f"\n   Topics avec score > 0: {topics_with_score}/{topics.count()}")
        
    except Category.DoesNotExist:
        print("❌ Catégorie 'annonces' introuvable")

if __name__ == '__main__':
    main()
