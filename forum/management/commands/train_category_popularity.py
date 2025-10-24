"""
Commande Django pour entraîner le modèle de prédiction de popularité des catégories
"""

from django.core.management.base import BaseCommand
from forum.ai_category_predictor import category_predictor


class Command(BaseCommand):
    help = 'Entraîne le modèle de prédiction de popularité des catégories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=int,
            default=30,
            help='Période d\'analyse en jours (défaut: 30)'
        )
        
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Proportion des données pour le test (défaut: 0.2)'
        )

    def handle(self, *args, **options):
        period_days = options['period']
        test_size = options['test_size']
        
        self.stdout.write(self.style.WARNING(
            f'\n{"="*60}\n'
            f'🎓 ENTRAÎNEMENT DU MODÈLE DE PRÉDICTION DES CATÉGORIES\n'
            f'{"="*60}\n'
        ))
        
        self.stdout.write(f"📅 Période d'analyse: {period_days} jours")
        self.stdout.write(f"📊 Test size: {test_size}\n")
        
        try:
            # Entraîner le modèle
            metrics = category_predictor.train_model(test_size=test_size)
            
            self.stdout.write(self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'✅ ENTRAÎNEMENT RÉUSSI!\n'
                f'{"="*60}\n'
            ))
            
            self.stdout.write(f"📊 Accuracy: {metrics['accuracy']:.2%}")
            self.stdout.write(f"📈 Échantillons: {metrics['n_samples']}")
            self.stdout.write(f"🔢 Features: {metrics['n_features']}\n")
            
            # Top features
            self.stdout.write(self.style.WARNING("🎯 Top 5 features les plus importantes:"))
            for i, feat in enumerate(metrics['feature_importance'][:5], 1):
                self.stdout.write(f"   {i}. {feat['feature']}: {feat['importance']:.4f}")
            
            self.stdout.write(self.style.SUCCESS(
                f'\n💾 Modèle sauvegardé avec succès!'
                f'\n\n💡 Utilisez maintenant les prédictions dans vos vues:\n'
                f'   from forum.ai_category_predictor import category_predictor\n'
                f'   predictions = category_predictor.predict_all_categories()\n'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erreur: {str(e)}'))
            raise
