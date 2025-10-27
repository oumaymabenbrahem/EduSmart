"""
Vues Django pour les prédictions de popularité des catégories
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from forum.models import Category
from forum.ai_category_predictor import category_predictor


@require_http_methods(["GET"])
def category_popularity_api(request, category_id=None):
    """
    API endpoint pour obtenir la prédiction de popularité d'une catégorie
    
    GET /forum/api/category-popularity/ -> Toutes les catégories
    GET /forum/api/category-popularity/5/ -> Catégorie spécifique
    """
    try:
        if category_id:
            # Prédiction pour une catégorie spécifique
            category = get_object_or_404(Category, id=category_id, is_active=True)
            prediction = category_predictor.predict_popularity(category)
            
            return JsonResponse({
                'success': True,
                'prediction': prediction
            })
        else:
            # Prédictions pour toutes les catégories
            predictions = category_predictor.predict_all_categories()
            
            return JsonResponse({
                'success': True,
                'predictions': predictions,
                'total': len(predictions),
                'timestamp': timezone.now().isoformat()
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def categories_dashboard(request):
    """
    Dashboard admin pour visualiser la popularité des catégories
    """
    try:
        # Obtenir toutes les prédictions
        predictions = category_predictor.predict_all_categories()
        
        # Catégories en tendance
        trending = category_predictor.get_trending_categories(top_n=5)
        
        # Recommandations
        recommendations = category_predictor.get_recommendations()
        
        # Statistiques globales
        total_categories = len(predictions)
        very_popular_count = sum(1 for p in predictions if p['prediction'] == 0)
        popular_count = sum(1 for p in predictions if p['prediction'] == 1)
        average_count = sum(1 for p in predictions if p['prediction'] == 2)
        low_count = sum(1 for p in predictions if p['prediction'] == 3)
        
        context = {
            'predictions': predictions,
            'trending': trending,
            'recommendations': recommendations,
            'stats': {
                'total': total_categories,
                'very_popular': very_popular_count,
                'popular': popular_count,
                'average': average_count,
                'low': low_count,
            },
            'timestamp': timezone.now()
        }
        
        return render(request, 'forum/categories_dashboard.html', context)
        
    except Exception as e:
        return render(request, 'forum/categories_dashboard.html', {
            'error': str(e),
            'predictions': [],
            'trending': [],
        })


@staff_member_required
def trending_categories(request):
    """
    Page des catégories en tendance
    """
    try:
        trending = category_predictor.get_trending_categories(top_n=10)
        
        context = {
            'trending_categories': trending,
            'timestamp': timezone.now()
        }
        
        return render(request, 'forum/trending_categories.html', context)
        
    except Exception as e:
        return render(request, 'forum/trending_categories.html', {
            'error': str(e),
            'trending_categories': [],
        })


@require_http_methods(["GET"])
def compare_categories_api(request):
    """
    API pour comparer deux catégories
    
    GET /forum/api/compare-categories/?cat1=1&cat2=2
    """
    try:
        cat1_id = request.GET.get('cat1')
        cat2_id = request.GET.get('cat2')
        
        if not cat1_id or not cat2_id:
            return JsonResponse({
                'success': False,
                'error': 'Paramètres cat1 et cat2 requis'
            }, status=400)
        
        category1 = get_object_or_404(Category, id=cat1_id, is_active=True)
        category2 = get_object_or_404(Category, id=cat2_id, is_active=True)
        
        comparison = category_predictor.compare_categories(category1, category2)
        
        return JsonResponse({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def category_recommendations(request):
    """
    Page des recommandations de catégories
    """
    try:
        user = request.user if request.user.is_authenticated else None
        recommendations = category_predictor.get_recommendations(user=user)
        
        context = {
            'recommendations': recommendations,
            'timestamp': timezone.now()
        }
        
        return render(request, 'forum/category_recommendations.html', context)
        
    except Exception as e:
        return render(request, 'forum/category_recommendations.html', {
            'error': str(e),
            'recommendations': {},
        })


@staff_member_required
def category_popularity_stats(request):
    """
    Statistiques détaillées sur la popularité des catégories
    """
    try:
        predictions = category_predictor.predict_all_categories()
        
        # Calculer des statistiques
        import numpy as np
        
        scores = [p['popularity_score'] for p in predictions]
        momentums = [p['features']['momentum'] for p in predictions]
        engagement_rates = [p['features']['engagement_rate'] for p in predictions]
        
        stats = {
            'score': {
                'mean': float(np.mean(scores)),
                'median': float(np.median(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
            },
            'momentum': {
                'mean': float(np.mean(momentums)),
                'median': float(np.median(momentums)),
                'positive_count': sum(1 for m in momentums if m > 0),
                'negative_count': sum(1 for m in momentums if m < 0),
            },
            'engagement': {
                'mean': float(np.mean(engagement_rates)),
                'median': float(np.median(engagement_rates)),
                'high_engagement_count': sum(1 for e in engagement_rates if e > 5),
            }
        }
        
        context = {
            'predictions': predictions,
            'stats': stats,
            'timestamp': timezone.now()
        }
        
        return render(request, 'forum/category_stats.html', context)
        
    except Exception as e:
        return render(request, 'forum/category_stats.html', {
            'error': str(e),
            'predictions': [],
            'stats': {},
        })
