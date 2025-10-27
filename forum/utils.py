"""
Utilitaires pour optimiser les performances du forum
"""
from django.core.cache import cache
from django.db.models import Count, Q
from .models import Topic, Post, Category


def get_forum_statistics(force_refresh=False):
    """
    Récupère les statistiques du forum avec cache (5 minutes)
    
    Args:
        force_refresh: Force le recalcul même si en cache
        
    Returns:
        dict avec total_topics, total_posts, etc.
    """
    cache_key = 'forum_statistics'
    cache_timeout = 300  # 5 minutes
    
    if not force_refresh:
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return cached_stats
    
    # Calculer les statistiques
    stats = {
        'total_topics': Topic.objects.filter(is_active=True).count(),
        'total_posts': Post.objects.filter(is_active=True).count(),
    }
    
    # Mettre en cache
    cache.set(cache_key, stats, cache_timeout)
    return stats


def get_categories_with_counts(force_refresh=False):
    """
    Récupère les catégories avec compteurs (cache 10 minutes)
    
    Args:
        force_refresh: Force le recalcul même si en cache
        
    Returns:
        QuerySet de Category avec annotations
    """
    cache_key = 'forum_categories_counts'
    cache_timeout = 600  # 10 minutes
    
    if not force_refresh:
        cached_categories = cache.get(cache_key)
        if cached_categories:
            return cached_categories
    
    categories = Category.objects.filter(is_active=True).only(
        'id', 'name', 'slug', 'description', 'icon', 'order'
    ).annotate(
        topics_count=Count('topics', filter=Q(topics__is_active=True), distinct=True)
    ).order_by('order')
    
    # Convertir en liste pour cache
    categories_list = list(categories)
    cache.set(cache_key, categories_list, cache_timeout)
    
    return categories_list


def invalidate_forum_cache():
    """
    Invalide tous les caches du forum
    À appeler lors de la création/modification/suppression de contenus
    """
    cache.delete('forum_statistics')
    cache.delete('forum_categories_counts')


def get_recent_topics(limit=5):
    """
    Récupère les derniers topics actifs (cache 2 minutes)
    
    Args:
        limit: Nombre de topics à récupérer
        
    Returns:
        QuerySet de Topic
    """
    cache_key = f'forum_recent_topics_{limit}'
    cache_timeout = 120  # 2 minutes
    
    cached_topics = cache.get(cache_key)
    if cached_topics:
        return cached_topics
    
    topics = Topic.objects.filter(is_active=True).select_related(
        'author', 'category'
    ).only(
        'id', 'title', 'slug', 'created_at', 'updated_at', 'views',
        'author__username', 'category__name', 'category__slug'
    ).order_by('-updated_at')[:limit]
    
    topics_list = list(topics)
    cache.set(cache_key, topics_list, cache_timeout)
    
    return topics_list
