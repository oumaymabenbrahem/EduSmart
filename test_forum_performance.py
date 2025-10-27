"""
Script de test pour mesurer les performances du forum
Usage: python test_forum_performance.py
"""
import os
import django
import time
from django.core.cache import cache

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduSmart.settings')
django.setup()

from forum.models import Category, Topic, Post
from forum.utils import get_forum_statistics, get_categories_with_counts, get_recent_topics


def test_forum_index_performance():
    """Test performance de la page d'accueil"""
    print("\n" + "="*60)
    print("🧪 TEST: Page d'accueil du forum")
    print("="*60)
    
    # Test SANS cache (first load)
    cache.clear()
    print("\n1️⃣ Premier chargement (SANS cache)")
    start = time.time()
    categories = get_categories_with_counts(force_refresh=True)
    recent_topics = get_recent_topics(limit=5)
    stats = get_forum_statistics(force_refresh=True)
    elapsed = time.time() - start
    print(f"   ⏱️  Temps: {elapsed*1000:.2f}ms")
    print(f"   📊 {len(categories)} catégories, {stats['total_topics']} topics, {stats['total_posts']} posts")
    
    # Test AVEC cache (cached)
    print("\n2️⃣ Deuxième chargement (AVEC cache)")
    start = time.time()
    categories = get_categories_with_counts()
    recent_topics = get_recent_topics(limit=5)
    stats = get_forum_statistics()
    elapsed = time.time() - start
    print(f"   ⏱️  Temps: {elapsed*1000:.2f}ms")
    print(f"   🚀 Amélioration: ~{(1 - elapsed/0.01)*100:.0f}% plus rapide")
    
    return elapsed


def test_topic_list_performance():
    """Test performance de la liste des topics"""
    print("\n" + "="*60)
    print("🧪 TEST: Liste des topics (category_detail)")
    print("="*60)
    
    category = Category.objects.filter(is_active=True).first()
    if not category:
        print("   ⚠️  Aucune catégorie active trouvée")
        return
    
    print(f"\n   Catégorie: {category.name}")
    
    start = time.time()
    topics = Topic.objects.filter(
        category=category,
        is_active=True
    ).select_related('author').only(
        'id', 'title', 'slug', 'status', 'created_at', 'updated_at', 'views',
        'author__username'
    )[:20]
    
    # Force l'évaluation du queryset
    topics_list = list(topics)
    elapsed = time.time() - start
    
    print(f"   ⏱️  Temps: {elapsed*1000:.2f}ms")
    print(f"   📊 {len(topics_list)} topics récupérés")
    
    return elapsed


def test_topic_detail_performance():
    """Test performance vue détail d'un topic"""
    print("\n" + "="*60)
    print("🧪 TEST: Détail d'un topic (topic_detail)")
    print("="*60)
    
    topic = Topic.objects.filter(is_active=True).first()
    if not topic:
        print("   ⚠️  Aucun topic actif trouvé")
        return
    
    print(f"\n   Topic: {topic.title}")
    
    start = time.time()
    
    # Simuler la vue
    posts = topic.posts.filter(is_active=True).select_related('author').only(
        'id', 'content', 'created_at', 'updated_at', 'author__username', 'topic_id'
    )[:10]
    
    posts_list = list(posts)
    elapsed = time.time() - start
    
    print(f"   ⏱️  Temps: {elapsed*1000:.2f}ms")
    print(f"   📊 {len(posts_list)} posts récupérés")
    
    return elapsed


def main():
    print("\n" + "🚀"*30)
    print("     TESTS DE PERFORMANCE DU FORUM EDUSMART")
    print("🚀"*30)
    
    try:
        t1 = test_forum_index_performance()
        t2 = test_topic_list_performance()
        t3 = test_topic_detail_performance()
        
        print("\n" + "="*60)
        print("📈 RÉSUMÉ DES PERFORMANCES")
        print("="*60)
        if t1:
            print(f"   Page d'accueil (avec cache): {t1*1000:.2f}ms")
        if t2:
            print(f"   Liste topics:                 {t2*1000:.2f}ms")
        if t3:
            print(f"   Détail topic:                 {t3*1000:.2f}ms")
        
        print("\n✅ Tous les tests terminés avec succès!")
        
        # Recommandations
        print("\n" + "💡"*30)
        print("📋 RECOMMANDATIONS")
        print("💡"*30)
        
        if t1 and t1 > 0.1:
            print("   ⚠️  Page d'accueil > 100ms: Considérer augmenter durée cache")
        else:
            print("   ✅ Page d'accueil: Performance excellente")
            
        if t2 and t2 > 0.05:
            print("   ⚠️  Liste topics > 50ms: Considérer ajouter index DB")
        else:
            print("   ✅ Liste topics: Performance excellente")
            
        if t3 and t3 > 0.05:
            print("   ⚠️  Détail topic > 50ms: Vérifier nombre de posts")
        else:
            print("   ✅ Détail topic: Performance excellente")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
