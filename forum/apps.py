from django.apps import AppConfig


class ForumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forum'
    verbose_name = 'Forum & Discussions'
    
    def ready(self):
        """
        Code exécuté au démarrage de Django
        Initialise automatiquement les scores de popularité
        """
        import os
        from django.conf import settings
        
        # Éviter l'exécution pendant les migrations
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        try:
            from django.db.utils import OperationalError, ProgrammingError
            from .models import Topic
            from .ai_popularity_predictor import TopicPopularityPredictor
            
            # Vérifier si les tables existent
            try:
                topics_count = Topic.objects.count()
            except (OperationalError, ProgrammingError):
                # Tables pas encore créées (première installation)
                return
            
            # Initialiser les scores si nécessaire
            topics_without_score = Topic.objects.filter(
                is_active=True,
                popularity_score=0.0
            ).count()
            
            if topics_without_score > 0:
                print(f"\n🔄 Initialisation automatique des scores de popularité...")
                print(f"📊 {topics_without_score} topics à traiter")
                
                predictor = TopicPopularityPredictor()
                topics = Topic.objects.filter(is_active=True, popularity_score=0.0)[:100]
                
                updated = 0
                for topic in topics:
                    try:
                        predictor.update_topic_popularity(topic)
                        updated += 1
                    except Exception as e:
                        pass
                
                print(f"✅ {updated} scores initialisés automatiquement\n")
            
        except Exception as e:
            # Ne pas bloquer le démarrage en cas d'erreur
            print(f"⚠ Info: Initialisation des scores ignorée ({e})")
