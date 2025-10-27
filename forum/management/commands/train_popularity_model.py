"""
Commande de management pour entraîner le modèle de prédiction de popularité
Usage: python manage.py train_popularity_model
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import os
import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class Command(BaseCommand):
    help = 'Entraîne le modèle ML de prédiction de popularité des topics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours de données historiques à utiliser (défaut: 30)'
        )
        parser.add_argument(
            '--min-age',
            type=int,
            default=12,
            help='Âge minimum en heures des topics pour avoir des données (défaut: 12h)'
        )

    def handle(self, *args, **options):
        if not SKLEARN_AVAILABLE:
            self.stdout.write(self.style.ERROR(
                '❌ scikit-learn n\'est pas installé. Installez-le avec: pip install scikit-learn'
            ))
            return

        days = options['days']
        min_age_hours = options['min_age']
        
        self.stdout.write(self.style.WARNING(f'🔄 Entraînement du modèle avec {days} jours de données...'))
        
        # Importer ici pour éviter les erreurs d'import circulaire
        from forum.models import Topic, Post
        
        # 1. Collecter les données historiques
        cutoff_date = timezone.now() - timedelta(days=days)
        min_age_date = timezone.now() - timedelta(hours=min_age_hours)
        
        topics = Topic.objects.filter(
            is_active=True,
            created_at__gte=cutoff_date,
            created_at__lte=min_age_date
        ).select_related('author', 'category').prefetch_related('posts')
        
        if topics.count() < 10:
            self.stdout.write(self.style.ERROR(
                f'❌ Pas assez de données historiques (seulement {topics.count()} topics). '
                f'Minimum requis: 10 topics.'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✓ {topics.count()} topics trouvés pour l\'entraînement'))
        
        # 2. Extraire les features et labels
        data = []
        for topic in topics:
            try:
                features = self.extract_features(topic)
                label = self.calculate_engagement(topic)
                data.append({**features, 'engagement_score': label})
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ Erreur pour topic {topic.id}: {e}'))
                continue
        
        if len(data) < 10:
            self.stdout.write(self.style.ERROR('❌ Pas assez de données valides pour entraîner le modèle'))
            return
        
        df = pd.DataFrame(data)
        self.stdout.write(self.style.SUCCESS(f'✓ Dataset créé: {len(df)} exemples'))
        
        # 3. Séparer features et labels
        feature_columns = [col for col in df.columns if col != 'engagement_score']
        X = df[feature_columns]
        y = df['engagement_score']
        
        # 4. Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 5. Entraîner le modèle
        self.stdout.write(self.style.WARNING('🔄 Entraînement du modèle RandomForest...'))
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # 6. Évaluer le modèle
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)
        
        self.stdout.write(self.style.SUCCESS('✓ Modèle entraîné avec succès !'))
        self.stdout.write(f'  📊 MAE Train: {train_mae:.2f} | Test: {test_mae:.2f}')
        self.stdout.write(f'  📊 R² Train: {train_r2:.3f} | Test: {test_r2:.3f}')
        
        # 7. Importance des features
        feature_importance = pd.DataFrame({
            'feature': feature_columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.stdout.write(self.style.SUCCESS('\n📈 Top 5 features les plus importantes:'))
        for idx, row in feature_importance.head(5).iterrows():
            self.stdout.write(f'  • {row["feature"]}: {row["importance"]:.3f}')
        
        # 8. Sauvegarder le modèle
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'ml_models')
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, 'topic_popularity_model.pkl')
        joblib.dump(model, model_path)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Modèle sauvegardé dans: {model_path}'))
        self.stdout.write(self.style.SUCCESS('✓ Vous pouvez maintenant mettre à jour les scores avec: python manage.py update_popularity_scores'))
    
    def extract_features(self, topic):
        """Extrait les features d'un topic pour l'entraînement"""
        now = timezone.now()
        topic_age_hours = (now - topic.created_at).total_seconds() / 3600
        
        # Compter posts et likes
        posts_count = topic.posts.filter(is_active=True).count()
        likes_count = sum([post.likes.count() for post in topic.posts.filter(is_active=True)])
        
        # Activité récente
        h6_ago = topic.created_at + timedelta(hours=6)
        h24_ago = topic.created_at + timedelta(hours=24)
        h48_ago = topic.created_at + timedelta(hours=48)
        
        posts_first_6h = topic.posts.filter(
            created_at__gte=topic.created_at,
            created_at__lte=h6_ago,
            is_active=True
        ).count()
        
        posts_first_24h = topic.posts.filter(
            created_at__gte=topic.created_at,
            created_at__lte=h24_ago,
            is_active=True
        ).count()
        
        posts_first_48h = topic.posts.filter(
            created_at__gte=topic.created_at,
            created_at__lte=h48_ago,
            is_active=True
        ).count()
        
        # Stats auteur
        author_topics = topic.author.topics.filter(is_active=True).count()
        author_posts = topic.author.posts.filter(is_active=True).count()
        
        # Stats catégorie
        category_topics = topic.category.topics.filter(is_active=True).count()
        
        # Features textuelles simples
        title_length = len(topic.title)
        content_length = len(topic.content)
        has_tags = 1 if topic.tags else 0
        
        return {
            'topic_age_hours': topic_age_hours,
            'views': topic.views,
            'posts_count': posts_count,
            'likes_count': likes_count,
            'posts_first_6h': posts_first_6h,
            'posts_first_24h': posts_first_24h,
            'posts_first_48h': posts_first_48h,
            'posts_per_hour': posts_count / max(topic_age_hours, 1.0),
            'author_reputation': author_topics + author_posts,
            'category_size': category_topics,
            'is_pinned': 1 if topic.status == 'pinned' else 0,
            'has_solution': 1 if topic.posts.filter(is_solution=True).exists() else 0,
            'title_length': title_length,
            'content_length': content_length,
            'has_tags': has_tags,
        }
    
    def calculate_engagement(self, topic):
        """
        Calcule un score d'engagement pour un topic
        Combine vues, réponses et likes avec des poids
        """
        posts_count = topic.posts.filter(is_active=True).count()
        likes_count = sum([post.likes.count() for post in topic.posts.filter(is_active=True)])
        
        # Score pondéré
        engagement = (
            topic.views * 1.0 +
            posts_count * 5.0 +
            likes_count * 3.0
        )
        
        return engagement
