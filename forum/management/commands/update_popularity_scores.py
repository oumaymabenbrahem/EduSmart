"""
Commande pour mettre à jour les scores de popularité des topics
Usage: python manage.py update_popularity_scores
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Met à jour les scores de popularité de tous les topics récents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=48,
            help='Nombre d\'heures de topics à mettre à jour (défaut: 48h)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limite du nombre de topics à traiter'
        )
        parser.add_argument(
            '--category',
            type=str,
            default=None,
            help='Slug de la catégorie à traiter (optionnel)'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        limit = options['limit']
        category_slug = options['category']
        
        self.stdout.write(self.style.WARNING(f'🔄 Mise à jour des scores de popularité...'))
        
        # Importer le prédicteur
        try:
            from forum.ai_popularity_predictor import TopicPopularityPredictor
        except ImportError:
            self.stdout.write(self.style.ERROR(
                '❌ Impossible d\'importer le module ai_popularity_predictor'
            ))
            return
        
        # Importer les modèles
        from forum.models import Topic, Category
        
        # Filtrer par catégorie si spécifié
        queryset = Topic.objects.filter(is_active=True)
        
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                queryset = queryset.filter(category=category)
                self.stdout.write(f'  📂 Catégorie: {category.name}')
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Catégorie "{category_slug}" introuvable'))
                return
        
        # Filtrer par date
        cutoff_date = timezone.now() - timedelta(hours=hours)
        queryset = queryset.filter(created_at__gte=cutoff_date)
        
        if limit:
            queryset = queryset[:limit]
        
        total_count = queryset.count()
        self.stdout.write(f'  📊 Topics à traiter: {total_count}')
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠ Aucun topic à mettre à jour'))
            return
        
        # Initialiser le prédicteur
        predictor = TopicPopularityPredictor()
        
        # Mettre à jour les topics
        updated = 0
        errors = 0
        
        for topic in queryset.select_related('author', 'category').prefetch_related('posts'):
            try:
                score = predictor.update_topic_popularity(topic)
                updated += 1
                
                if updated % 10 == 0:
                    self.stdout.write(f'  ⏳ Progression: {updated}/{total_count}')
            
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.WARNING(f'  ⚠ Erreur topic {topic.id}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Terminé !'))
        self.stdout.write(f'  ✅ Topics mis à jour: {updated}')
        if errors > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠ Erreurs: {errors}'))
