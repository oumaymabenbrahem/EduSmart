"""
Système de Prédiction de Popularité des Catégories
===================================================

Ce module utilise le Machine Learning pour prédire quelle catégorie sera la plus populaire
en se basant sur :
- Nombre de vues totales
- Nombre de topics
- Nombre de posts/commentaires
- Taux d'engagement
- Tendance de croissance
- Temps de réponse moyen

Modèle : Random Forest Classifier (classification multi-classe)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import os
from typing import Dict, List, Tuple, Optional


class CategoryPopularityPredictor:
    """
    Prédicteur de popularité des catégories
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.category_mapping = {}  # ID catégorie -> nom
        self.model_path = 'ml_models/category_popularity_model.pkl'
        self.scaler_path = 'ml_models/category_popularity_scaler.pkl'
        
        # Créer le dossier ml_models s'il n'existe pas
        os.makedirs('ml_models', exist_ok=True)
    
    
    def extract_category_features(self, category, period_days=30) -> Dict[str, float]:
        """
        Extrait les features d'une catégorie pour la prédiction
        
        Args:
            category: Instance de Category
            period_days: Période d'analyse en jours
            
        Returns:
            Dict avec toutes les features
        """
        from forum.models import Topic, Post
        
        now = timezone.now()
        period_start = now - timedelta(days=period_days)
        
        # Topics de la catégorie
        topics = category.topics.filter(is_active=True)
        recent_topics = topics.filter(created_at__gte=period_start)
        
        # --- FEATURES QUANTITATIVES ---
        
        # 1. Nombre total de topics
        total_topics = topics.count()
        recent_topics_count = recent_topics.count()
        
        # 2. Vues totales
        total_views = topics.aggregate(total=Sum('views'))['total'] or 0
        avg_views_per_topic = total_views / total_topics if total_topics > 0 else 0
        
        # 3. Posts et commentaires
        total_posts = Post.objects.filter(topic__category=category, is_active=True).count()
        avg_posts_per_topic = total_posts / total_topics if total_topics > 0 else 0
        
        # 4. Taux d'engagement (posts / vues)
        engagement_rate = (total_posts / total_views * 100) if total_views > 0 else 0
        
        # --- FEATURES TEMPORELLES ---
        
        # 5. Activité récente (30 derniers jours)
        recent_posts = Post.objects.filter(
            topic__category=category,
            is_active=True,
            created_at__gte=period_start
        ).count()
        
        # 6. Taux de croissance des topics
        old_period_start = period_start - timedelta(days=period_days)
        old_topics_count = topics.filter(
            created_at__gte=old_period_start,
            created_at__lt=period_start
        ).count()
        
        growth_rate = ((recent_topics_count - old_topics_count) / old_topics_count * 100) \
                     if old_topics_count > 0 else 0
        
        # --- FEATURES ENGAGEMENT UTILISATEURS ---
        
        # 7. Nombre d'auteurs uniques
        unique_authors = topics.values('author').distinct().count()
        
        # 8. Diversité des auteurs (auteurs uniques / topics)
        author_diversity = (unique_authors / total_topics * 100) if total_topics > 0 else 0
        
        # 9. Topics avec solutions
        solved_topics = topics.filter(posts__is_solution=True).distinct().count()
        solve_rate = (solved_topics / total_topics * 100) if total_topics > 0 else 0
        
        # --- FEATURES TEMPS DE RÉPONSE ---
        
        # 10. Temps moyen de première réponse (en heures)
        response_times = []
        for topic in recent_topics[:50]:  # Échantillon de 50 topics
            first_post = topic.posts.filter(is_active=True).order_by('created_at').first()
            second_post = topic.posts.filter(is_active=True).order_by('created_at')[1:2].first()
            
            if second_post:
                time_diff = (second_post.created_at - first_post.created_at).total_seconds() / 3600
                response_times.append(time_diff)
        
        avg_response_time = np.mean(response_times) if response_times else 24.0
        
        # --- FEATURES LIKES ET POPULARITÉ ---
        
        # 11. Likes moyens par post
        posts_with_likes = Post.objects.filter(
            topic__category=category,
            is_active=True
        )
        
        total_likes = sum([post.likes_count for post in posts_with_likes[:100]])  # Échantillon
        avg_likes = total_likes / min(100, posts_with_likes.count()) if posts_with_likes.exists() else 0
        
        # --- FEATURES TENDANCES ---
        
        # 12. Pics d'activité (jours avec beaucoup d'activité)
        activity_by_day = {}
        for i in range(period_days):
            day_start = now - timedelta(days=i+1)
            day_end = now - timedelta(days=i)
            
            day_posts = Post.objects.filter(
                topic__category=category,
                is_active=True,
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count()
            
            activity_by_day[i] = day_posts
        
        # Jours avec activité > moyenne
        mean_activity = np.mean(list(activity_by_day.values()))
        peak_days = sum(1 for v in activity_by_day.values() if v > mean_activity * 1.5)
        
        # 13. Régularité de l'activité (écart-type faible = régulier)
        activity_std = np.std(list(activity_by_day.values()))
        activity_regularity = 1 / (activity_std + 1)  # Plus proche de 1 = plus régulier
        
        # --- FEATURES COMPARATIVES ---
        
        # 14. Rang de la catégorie (par nombre de topics)
        from forum.models import Category
        all_categories = Category.objects.filter(is_active=True).annotate(
            topic_count=Count('topics')
        ).order_by('-topic_count')
        
        category_rank = list(all_categories).index(category) + 1 if category in all_categories else 99
        
        # 15. Part de marché (% de tous les topics du forum)
        total_forum_topics = Topic.objects.filter(is_active=True).count()
        market_share = (total_topics / total_forum_topics * 100) if total_forum_topics > 0 else 0
        
        # --- FEATURES MOMENTUM ---
        
        # 16. Momentum score (activité cette semaine vs semaine dernière)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        this_week_posts = Post.objects.filter(
            topic__category=category,
            is_active=True,
            created_at__gte=week_ago
        ).count()
        
        last_week_posts = Post.objects.filter(
            topic__category=category,
            is_active=True,
            created_at__gte=two_weeks_ago,
            created_at__lt=week_ago
        ).count()
        
        momentum = ((this_week_posts - last_week_posts) / last_week_posts * 100) \
                   if last_week_posts > 0 else 0
        
        # --- FEATURES VUES ---
        
        # 17. Vues récentes (30 derniers jours)
        recent_views = recent_topics.aggregate(total=Sum('views'))['total'] or 0
        
        # 18. Vues par topic récent
        views_per_recent_topic = recent_views / recent_topics_count if recent_topics_count > 0 else 0
        
        # Retourner toutes les features
        features = {
            # Quantitatives
            'total_topics': total_topics,
            'recent_topics_count': recent_topics_count,
            'total_views': total_views,
            'avg_views_per_topic': avg_views_per_topic,
            'total_posts': total_posts,
            'avg_posts_per_topic': avg_posts_per_topic,
            'engagement_rate': engagement_rate,
            
            # Temporelles
            'recent_posts': recent_posts,
            'growth_rate': growth_rate,
            
            # Engagement utilisateurs
            'unique_authors': unique_authors,
            'author_diversity': author_diversity,
            'solve_rate': solve_rate,
            
            # Temps de réponse
            'avg_response_time': avg_response_time,
            
            # Likes
            'avg_likes': avg_likes,
            
            # Tendances
            'peak_days': peak_days,
            'activity_regularity': activity_regularity,
            
            # Comparatives
            'category_rank': category_rank,
            'market_share': market_share,
            
            # Momentum
            'momentum': momentum,
            'recent_views': recent_views,
            'views_per_recent_topic': views_per_recent_topic,
        }
        
        return features
    
    
    def prepare_training_data(self, period_days=30) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prépare les données d'entraînement
        
        Returns:
            X, y : features et labels
        """
        from forum.models import Category
        
        categories = Category.objects.filter(is_active=True)
        
        if categories.count() < 3:
            raise ValueError("Au moins 3 catégories sont nécessaires pour l'entraînement")
        
        X_data = []
        y_data = []
        self.category_mapping = {}
        
        # Extraire features pour chaque catégorie
        category_scores = []
        for category in categories:
            features = self.extract_category_features(category, period_days)
            
            # Calculer un score de popularité composite
            popularity_score = (
                features['total_views'] * 0.3 +
                features['total_posts'] * 0.25 +
                features['engagement_rate'] * 10 +
                features['recent_posts'] * 0.2 +
                features['momentum'] * 0.15 +
                features['market_share'] * 5
            )
            
            category_scores.append({
                'id': category.id,
                'name': category.name,
                'score': popularity_score,
                'features': features
            })
            
            self.category_mapping[category.id] = category.name
        
        # Trier par score et assigner des labels
        category_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Labels : 0 = Très populaire, 1 = Populaire, 2 = Moyenne, 3 = Faible
        n_categories = len(category_scores)
        
        for idx, cat_data in enumerate(category_scores):
            features_dict = cat_data['features']
            feature_values = [features_dict[k] for k in sorted(features_dict.keys())]
            
            X_data.append(feature_values)
            
            # Assigner label selon le rang
            if idx < n_categories * 0.25:
                label = 0  # Très populaire (top 25%)
            elif idx < n_categories * 0.5:
                label = 1  # Populaire (25-50%)
            elif idx < n_categories * 0.75:
                label = 2  # Moyenne (50-75%)
            else:
                label = 3  # Faible (bottom 25%)
            
            y_data.append(label)
        
        # Stocker les noms des features
        if X_data:
            self.feature_names = sorted(category_scores[0]['features'].keys())
        
        return np.array(X_data), np.array(y_data)
    
    
    def train_model(self, test_size=0.2, random_state=42) -> Dict[str, float]:
        """
        Entraîne le modèle de classification
        
        Returns:
            Dict avec les métriques de performance
        """
        print("🔄 Préparation des données...")
        X, y = self.prepare_training_data()
        
        if len(X) < 5:
            raise ValueError("Au moins 5 échantillons sont nécessaires pour l'entraînement")
        
        print(f"✅ {len(X)} catégories analysées")
        print(f"📊 Features extraites : {len(self.feature_names)}")
        
        # Split train/test avec adaptation pour petits datasets
        if len(X) < 10:
            # Pour moins de 10 échantillons, utiliser un split plus petit
            test_size = 0.2 if len(X) >= 8 else 0.1
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, shuffle=True
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
        
        # Normalisation
        print("🔄 Normalisation des features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Entraînement
        print("🔄 Entraînement du modèle Random Forest...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            class_weight='balanced'
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Métriques
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✅ Modèle entraîné avec succès!")
        print(f"📊 Accuracy: {accuracy:.2%}")
        print("\n📋 Rapport de classification:")
        
        # Obtenir les classes uniques et leurs noms
        unique_classes = sorted(set(y_train) | set(y_test))
        class_names = ['Très populaire', 'Populaire', 'Moyenne', 'Faible']
        target_names = [class_names[i] for i in unique_classes]
        
        print(classification_report(y_test, y_pred, 
                                   labels=unique_classes,
                                   target_names=target_names,
                                   zero_division=0))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🎯 Top 10 features les plus importantes:")
        print(feature_importance.head(10))
        
        # Sauvegarder le modèle
        self.save_model()
        
        return {
            'accuracy': accuracy,
            'n_samples': len(X),
            'n_features': len(self.feature_names),
            'feature_importance': feature_importance.to_dict('records')
        }
    
    
    def predict_popularity(self, category) -> Dict:
        """
        Prédit la popularité d'une catégorie
        
        Args:
            category: Instance de Category
            
        Returns:
            Dict avec la prédiction et les détails
        """
        if self.model is None:
            self.load_model()
        
        # Extraire features
        features = self.extract_category_features(category)
        feature_values = np.array([[features[k] for k in sorted(features.keys())]])
        
        # Normaliser
        feature_values_scaled = self.scaler.transform(feature_values)
        
        # Prédire
        prediction = self.model.predict(feature_values_scaled)[0]
        probabilities = self.model.predict_proba(feature_values_scaled)[0]
        
        # Labels
        labels = ['Très populaire', 'Populaire', 'Moyenne', 'Faible']
        emojis = ['🔥', '⭐', '📊', '💤']
        colors = ['success', 'info', 'warning', 'secondary']
        
        return {
            'category_id': category.id,
            'category_name': category.name,
            'prediction': prediction,
            'prediction_label': labels[prediction],
            'prediction_emoji': emojis[prediction],
            'prediction_color': colors[prediction],
            'confidence': float(probabilities[prediction] * 100),
            'probabilities': {
                labels[i]: float(probabilities[i] * 100)
                for i in range(len(labels))
            },
            'features': features,
            'popularity_score': float(
                features['total_views'] * 0.3 +
                features['total_posts'] * 0.25 +
                features['engagement_rate'] * 10 +
                features['recent_posts'] * 0.2 +
                features['momentum'] * 0.15
            )
        }
    
    
    def predict_all_categories(self) -> List[Dict]:
        """
        Prédit la popularité de toutes les catégories
        
        Returns:
            Liste des prédictions triée par popularité
        """
        from forum.models import Category
        
        categories = Category.objects.filter(is_active=True)
        predictions = []
        
        for category in categories:
            try:
                prediction = self.predict_popularity(category)
                predictions.append(prediction)
            except Exception as e:
                print(f"❌ Erreur pour {category.name}: {str(e)}")
        
        # Trier par score de popularité
        predictions.sort(key=lambda x: x['popularity_score'], reverse=True)
        
        # Ajouter le rang
        for idx, pred in enumerate(predictions):
            pred['rank'] = idx + 1
        
        return predictions
    
    
    def get_trending_categories(self, top_n=5) -> List[Dict]:
        """
        Retourne les catégories en tendance (momentum positif)
        
        Args:
            top_n: Nombre de catégories à retourner
            
        Returns:
            Liste des catégories en tendance
        """
        predictions = self.predict_all_categories()
        
        # Filtrer celles avec momentum > 0 et trier
        trending = [p for p in predictions if p['features']['momentum'] > 0]
        trending.sort(key=lambda x: x['features']['momentum'], reverse=True)
        
        return trending[:top_n]
    
    
    def get_recommendations(self, user=None) -> Dict:
        """
        Recommande des catégories à explorer
        
        Args:
            user: Instance de User (optionnel)
            
        Returns:
            Dict avec les recommandations
        """
        predictions = self.predict_all_categories()
        
        # Catégories très populaires
        very_popular = [p for p in predictions if p['prediction'] == 0][:3]
        
        # Catégories en croissance
        growing = sorted(
            predictions,
            key=lambda x: x['features']['growth_rate'],
            reverse=True
        )[:3]
        
        # Catégories actives
        active = sorted(
            predictions,
            key=lambda x: x['features']['recent_posts'],
            reverse=True
        )[:3]
        
        return {
            'very_popular': very_popular,
            'growing': growing,
            'most_active': active,
            'timestamp': timezone.now()
        }
    
    
    def compare_categories(self, category1, category2) -> Dict:
        """
        Compare deux catégories
        
        Returns:
            Dict avec la comparaison
        """
        pred1 = self.predict_popularity(category1)
        pred2 = self.predict_popularity(category2)
        
        winner = category1 if pred1['popularity_score'] > pred2['popularity_score'] else category2
        
        return {
            'category1': pred1,
            'category2': pred2,
            'winner': {
                'id': winner.id,
                'name': winner.name
            },
            'score_difference': abs(pred1['popularity_score'] - pred2['popularity_score'])
        }
    
    
    def save_model(self):
        """Sauvegarde le modèle et le scaler"""
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'category_mapping': self.category_mapping
            }, f)
        
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✅ Modèle sauvegardé dans {self.model_path}")
    
    
    def load_model(self):
        """Charge le modèle et le scaler"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                "Modèle non trouvé. Entraînez d'abord le modèle avec "
                "'python manage.py train_category_popularity'"
            )
        
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.feature_names = data['feature_names']
            self.category_mapping = data['category_mapping']
        
        with open(self.scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        print(f"✅ Modèle chargé depuis {self.model_path}")


# Instance globale
category_predictor = CategoryPopularityPredictor()
