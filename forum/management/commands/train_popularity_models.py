"""
Commande Django pour entraîner les modèles de prédiction de popularité
Usage: python manage.py train_popularity_models
"""

from django.core.management.base import BaseCommand
from forum.ai_popularity_predictor import get_predictor


class Command(BaseCommand):
    help = 'Entraîne les modèles de prédiction de popularité des topics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-samples',
            type=int,
            default=50,
            help='Nombre minimum de topics requis pour l\'entraînement (défaut: 50)',
        )

    def handle(self, *args, **options):
        min_samples = options['min_samples']
        
        self.stdout.write(self.style.WARNING(
            f'\n🤖 Entraînement des modèles de prédiction de popularité...\n'
        ))
        
        predictor = get_predictor()
        success = predictor.train_models(min_samples=min_samples)
        
        if success:
            self.stdout.write(self.style.SUCCESS(
                '\n✅ Modèles entraînés et sauvegardés avec succès!\n'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'\n❌ Échec de l\'entraînement. Vérifiez qu\'il y a au moins {min_samples} topics.\n'
            ))
