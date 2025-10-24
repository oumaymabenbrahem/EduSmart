"""
Vues pour les fonctionnalités de prédiction de popularité
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator

from .models import Topic, Category
from .ai_popularity_predictor import (
    get_predictor, 
    predict_topic_popularity,
    get_trending_topics
)
import json


@login_required
@require_http_methods(["POST"])
def predict_topic_api(request):
    """
    API pour prédire la popularité d'un topic en temps réel
    Utilisé lors de la création d'un topic (AJAX)
    """
    try:
        data = json.loads(request.body)
        
        title = data.get('title', '')
        content = data.get('content', '')
        category_id = data.get('category_id')
        
        if not title or not content or not category_id:
            return JsonResponse({
                'error': 'Titre, contenu et catégorie requis'
            }, status=400)
        
        # Faire la prédiction
        prediction = predict_topic_popularity(
            title=title,
            content=content,
            category_id=int(category_id),
            author_id=request.user.id
        )
        
        return JsonResponse({
            'success': True,
            'prediction': prediction
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
def topic_popularity_preview(request, topic_id):
    """
    Affiche l'analyse de popularité d'un topic existant
    """
    topic = get_object_or_404(Topic, id=topic_id, is_active=True)
    predictor = get_predictor()
    
    # Analyse de performance
    analysis = predictor.analyze_topic_performance(topic_id)
    
    # Prédiction actuelle
    prediction = predict_topic_popularity(
        title=topic.title,
        content=topic.first_post.content if topic.first_post else "",
        category_id=topic.category_id,
        author_id=topic.author_id
    )
    
    context = {
        'topic': topic,
        'analysis': analysis,
        'prediction': prediction,
    }
    
    return render(request, 'forum/topic_popularity_analysis.html', context)


@staff_member_required
def trending_topics_dashboard(request):
    """
    Dashboard admin des topics trending (surperformance)
    """
    trending = get_trending_topics(limit=20)
    
    context = {
        'trending_topics': trending,
    }
    
    return render(request, 'forum/trending_dashboard.html', context)


@staff_member_required
def popularity_stats(request):
    """
    Statistiques globales sur les prédictions
    """
    from django.db.models import Avg, Count
    from django.utils import timezone
    from datetime import timedelta
    
    predictor = get_predictor()
    
    # Topics récents (7 derniers jours)
    recent_topics = Topic.objects.filter(
        is_active=True,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('author', 'category')
    
    # Analyser chaque topic
    predictions = []
    for topic in recent_topics[:50]:
        analysis = predictor.analyze_topic_performance(topic.id)
        if 'error' not in analysis:
            predictions.append(analysis)
    
    # Calculer les métriques
    if predictions:
        avg_views_error = sum(abs(p['views_difference']) for p in predictions) / len(predictions)
        avg_posts_error = sum(abs(p['posts_difference']) for p in predictions) / len(predictions)
        
        overperforming = sum(1 for p in predictions if p['actual_views'] > p['predicted_views'] * 1.2)
        underperforming = sum(1 for p in predictions if p['actual_views'] < p['predicted_views'] * 0.8)
    else:
        avg_views_error = 0
        avg_posts_error = 0
        overperforming = 0
        underperforming = 0
    
    # Statistiques générales
    total_topics = Topic.objects.filter(is_active=True).count()
    avg_views = Topic.objects.filter(is_active=True).aggregate(avg=Avg('views'))['avg'] or 0
    
    context = {
        'total_topics': total_topics,
        'recent_topics_count': recent_topics.count(),
        'avg_views': round(avg_views, 2),
        'avg_views_error': round(avg_views_error, 2),
        'avg_posts_error': round(avg_posts_error, 2),
        'overperforming': overperforming,
        'underperforming': underperforming,
        'predictions': predictions[:20],
        'model_status': 'Actif' if predictor.model_views else 'Non entraîné',
    }
    
    return render(request, 'forum/popularity_stats.html', context)


@login_required
def my_topics_predictions(request):
    """
    Affiche les prédictions pour tous les topics de l'utilisateur
    """
    predictor = get_predictor()
    
    topics_list = Topic.objects.filter(
        author=request.user,
        is_active=True
    ).select_related('category').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(topics_list, 10)
    page_number = request.GET.get('page')
    topics = paginator.get_page(page_number)
    
    # Ajouter les analyses
    for topic in topics:
        topic.analysis = predictor.analyze_topic_performance(topic.id)
    
    context = {
        'topics': topics,
    }
    
    return render(request, 'forum/my_topics_predictions.html', context)
