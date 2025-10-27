"""
Template tags personnalisés pour afficher la popularité des topics et catégories
"""

from django import template
from django.utils.safestring import mark_safe
from forum.ai_category_predictor import category_predictor

register = template.Library()


@register.simple_tag
def popularity_badge(topic):
    """
    Affiche un badge de popularité pour un topic
    
    Usage dans le template:
    {% load forum_tags %}
    {% popularity_badge topic %}
    """
    try:
        views = topic.views
        posts_count = topic.get_posts_count()
        
        # Calculer un score simple
        score = min(100, (views / 10) + (posts_count * 5))
        
        # Déterminer la catégorie et le style
        if score >= 80:
            badge_class = "danger"
            icon = "🔥"
            text = "Très populaire"
        elif score >= 60:
            badge_class = "success"
            icon = "⭐"
            text = "Populaire"
        elif score >= 40:
            badge_class = "info"
            icon = "📊"
            text = "Modéré"
        else:
            badge_class = "secondary"
            icon = "💤"
            text = "Calme"
        
        html = f'<span class="badge bg-{badge_class} bg-opacity-75">{icon} {text}</span>'
        return mark_safe(html)
        
    except Exception as e:
        return ""


@register.simple_tag
def trending_badge(topic):
    """
    Affiche un badge TRENDING si le topic surperforme
    
    Usage:
    {% trending_badge topic %}
    """
    try:
        from forum.ai_popularity_predictor import get_predictor
        
        predictor = get_predictor()
        analysis = predictor.analyze_topic_performance(topic.id)
        
        if 'error' not in analysis:
            actual = analysis['actual_views']
            predicted = analysis['predicted_views']
            
            # Si + de 50% au-dessus de la prédiction
            if actual > predicted * 1.5 and actual > 50:
                return mark_safe('<span class="badge bg-danger"><i class="bi bi-graph-up-arrow"></i> TRENDING</span>')
        
        return ""
    except:
        return ""


@register.filter
def popularity_score(topic):
    """
    Retourne le score de popularité (0-100) d'un topic
    
    Usage:
    {{ topic|popularity_score }}
    """
    try:
        views = topic.views
        posts_count = topic.get_posts_count()
        score = min(100, (views / 10) + (posts_count * 5))
        return round(score, 1)
    except:
        return 0


@register.filter
def popularity_class(topic):
    """
    Retourne la classe CSS Bootstrap pour la popularité
    
    Usage:
    <div class="bg-{{ topic|popularity_class }}">
    """
    try:
        score = popularity_score(topic)
        
        if score >= 80:
            return "danger"
        elif score >= 60:
            return "success"
        elif score >= 40:
            return "info"
        else:
            return "secondary"
    except:
        return "secondary"


@register.inclusion_tag('forum/includes/popularity_widget.html')
def show_popularity(topic):
    """
    Affiche un widget complet de popularité
    
    Usage:
    {% show_popularity topic %}
    """
    try:
        views = topic.views
        posts_count = topic.get_posts_count()
        score = min(100, (views / 10) + (posts_count * 5))
        
        # Déterminer la catégorie
        if score >= 80:
            category = "Très populaire"
            icon = "🔥"
            color = "danger"
        elif score >= 60:
            category = "Populaire"
            icon = "⭐"
            color = "success"
        elif score >= 40:
            category = "Modéré"
            icon = "📊"
            color = "info"
        else:
            category = "Calme"
            icon = "💤"
            color = "secondary"
        
        # Vérifier trending
        is_trending = False
        try:
            from forum.ai_popularity_predictor import get_predictor
            predictor = get_predictor()
            analysis = predictor.analyze_topic_performance(topic.id)
            
            if 'error' not in analysis:
                actual = analysis['actual_views']
                predicted = analysis['predicted_views']
                is_trending = actual > predicted * 1.5 and actual > 50
        except:
            pass
        
        return {
            'topic': topic,
            'score': round(score, 1),
            'category': category,
            'icon': icon,
            'color': color,
            'is_trending': is_trending,
            'views': views,
            'posts_count': posts_count
        }
    except Exception as e:
        return {
            'topic': topic,
            'score': 0,
            'category': 'N/A',
            'icon': '',
            'color': 'secondary',
            'is_trending': False
        }


@register.simple_tag
def popularity_bar(topic, show_label=True):
    """
    Affiche une barre de progression de popularité
    
    Usage:
    {% popularity_bar topic %}
    {% popularity_bar topic show_label=False %}
    """
    try:
        score = popularity_score(topic)
        color_class = popularity_class(topic)
        
        label = f'{score}/100' if show_label else ''
        
        html = f'''
        <div class="progress" style="height: 20px;">
            <div class="progress-bar bg-{color_class}" 
                 role="progressbar" 
                 style="width: {score}%"
                 aria-valuenow="{score}" 
                 aria-valuemin="0" 
                 aria-valuemax="100">
                {label}
            </div>
        </div>
        '''
        return mark_safe(html)
    except:
        return ""


# ============================================
# TEMPLATE TAGS POUR CATÉGORIES
# ============================================

@register.simple_tag
def category_popularity_badge(category):
    """
    Affiche un badge de popularité pour une catégorie
    
    Usage:
    {% load forum_tags %}
    {% category_popularity_badge category %}
    """
    try:
        prediction = category_predictor.predict_popularity(category)
        
        html = f'''<span class="badge badge-{prediction['prediction_color']} badge-pill">
            {prediction['prediction_emoji']} {prediction['prediction_label']}
        </span>'''
        
        return mark_safe(html)
    except:
        return ""


@register.simple_tag
def category_trending_badge(category):
    """
    Affiche un badge TRENDING si la catégorie a un momentum positif
    
    Usage:
    {% category_trending_badge category %}
    """
    try:
        prediction = category_predictor.predict_popularity(category)
        
        if prediction['features']['momentum'] > 10:
            html = '<span class="badge badge-warning">🚀 TRENDING</span>'
            return mark_safe(html)
        
        return ""
    except:
        return ""


@register.simple_tag
def category_popularity_score(category):
    """
    Retourne le score de popularité d'une catégorie (0-100)
    
    Usage:
    {% category_popularity_score category %}
    """
    try:
        prediction = category_predictor.predict_popularity(category)
        score = min(100, max(0, prediction['popularity_score']))
        return f"{score:.0f}"
    except:
        return "N/A"


@register.inclusion_tag('forum/includes/category_popularity_widget.html')
def show_category_popularity(category):
    """
    Affiche un widget complet avec toutes les infos de popularité
    
    Usage:
    {% show_category_popularity category %}
    """
    try:
        prediction = category_predictor.predict_popularity(category)
        return {
            'category': category,
            'prediction': prediction
        }
    except Exception as e:
        return {
            'category': category,
            'error': str(e)
        }


@register.simple_tag
def category_rank(category):
    """
    Retourne le rang de la catégorie parmi toutes les catégories
    
    Usage:
    {% category_rank category %}
    """
    try:
        predictions = category_predictor.predict_all_categories()
        for pred in predictions:
            if pred['category_id'] == category.id:
                return f"#{pred['rank']}"
        return "N/A"
    except:
        return "N/A"


@register.simple_tag
def category_momentum(category):
    """
    Affiche le momentum de la catégorie avec une flèche
    
    Usage:
    {% category_momentum category %}
    """
    try:
        prediction = category_predictor.predict_popularity(category)
        momentum = prediction['features']['momentum']
        
        if momentum > 0:
            html = f'<span class="text-success"><i class="ti-arrow-up"></i> +{momentum:.1f}%</span>'
        elif momentum < 0:
            html = f'<span class="text-danger"><i class="ti-arrow-down"></i> {momentum:.1f}%</span>'
        else:
            html = '<span class="text-muted">-</span>'
        
        return mark_safe(html)
    except:
        return ""


@register.simple_tag
def category_confidence(category):
    """
    Retourne le niveau de confiance de la prédiction (%)
    
    Usage:
    {% category_confidence category %}
    """
    try:
        prediction = category_predictor.predict_popularity(category)
        return f"{prediction['confidence']:.1f}%"
    except:
        return "N/A"


@register.simple_tag
def top_categories(limit=5):
    """
    Retourne les N catégories les plus populaires
    
    Usage:
    {% top_categories 5 %}
    """
    try:
        predictions = category_predictor.predict_all_categories()
        return predictions[:limit]
    except:
        return []

