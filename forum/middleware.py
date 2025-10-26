"""
Middleware pour rafraîchir automatiquement les scores de popularité
"""

import random
from django.utils import timezone
from datetime import timedelta


class PopularityRefreshMiddleware:
    """
    Rafraîchit aléatoirement quelques scores de popularité à chaque requête
    pour maintenir les données à jour sans surcharger le système
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.refresh_probability = 0.1  # 10% de chance par requête
        self.last_refresh = None
    
    def __call__(self, request):
        # Traiter la requête normalement
        response = self.get_response(request)
        
        # Rafraîchir les scores périodiquement (10% des requêtes)
        if random.random() < self.refresh_probability:
            self.refresh_random_topics()
        
        return response
    
    def refresh_random_topics(self):
        """Rafraîchit 5 topics aléatoires"""
        try:
            from forum.models import Topic
            from forum.ai_popularity_predictor import TopicPopularityPredictor
            
            # Éviter de rafraîchir trop souvent
            if self.last_refresh:
                if (timezone.now() - self.last_refresh).seconds < 60:
                    return
            
            # Sélectionner 5 topics aléatoires qui n'ont pas été rafraîchis récemment
            cutoff = timezone.now() - timedelta(hours=1)
            topics = Topic.objects.filter(
                is_active=True,
                popularity_refreshed_at__lt=cutoff
            ).order_by('?')[:5]
            
            if topics.exists():
                predictor = TopicPopularityPredictor()
                
                for topic in topics:
                    try:
                        predictor.update_topic_popularity(topic)
                    except Exception:
                        pass
                
                self.last_refresh = timezone.now()
        
        except Exception:
            # Ne pas casser l'application si erreur
            pass
