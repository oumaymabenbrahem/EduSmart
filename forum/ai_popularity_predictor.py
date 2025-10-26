"""
Module de prédiction de popularité des topics par Machine Learning
Prédit le nombre de vues et de réponses qu'un topic va recevoir
"""

import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Avg
from django.utils import timezone

# Imports conditionnels pour ML
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn non installé. Installez avec: pip install scikit-learn")

try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence-transformers non installé. Installez avec: pip install sentence-transformers")


class PopularityPredictor:
    """
    Prédit la popularité d'un topic basé sur :
    - Contenu du titre et description
    - Catégorie
    - Heure de publication
    - Historique de l'auteur
    - Tendances actuelles
    """
    
    def __init__(self):
        self.model_views = None
        self.model_posts = None
        self.scaler = StandardScaler()
        self.text_encoder = None
        self.models_dir = os.path.join(settings.BASE_DIR, 'forum', 'ml_models')
        
        # Créer le dossier des modèles si nécessaire
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Initialiser l'encodeur de texte
        if TRANSFORMERS_AVAILABLE:
            try:
                self.text_encoder = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            except:
                print("⚠️ Impossible de charger le modèle de texte")
        
        # Charger les modèles entraînés s'ils existent
        self.load_models()
    
    def extract_features(self, title: str, content: str, category_id: int, 
                        author_id: int, created_at: datetime = None) -> np.ndarray:
        """
        Extrait les features d'un topic pour la prédiction
        
        Returns:
            Array de features numériques
        """
        from forum.models import Topic, Post, Category
        from accounts.models import CustomUser
        
        features = []
        
        # === 1. FEATURES TEXTUELLES ===
        
        # Longueur du titre
        features.append(len(title))
        
        # Longueur du contenu
        features.append(len(content))
        
        # Nombre de mots dans le titre
        features.append(len(title.split()))
        
        # Nombre de mots dans le contenu
        features.append(len(content.split()))
        
        # Présence de point d'interrogation (question)
        features.append(1 if '?' in title or '?' in content else 0)
        
        # Présence de code (caractères spéciaux)
        code_indicators = ['```', 'def ', 'class ', 'import ', 'function', '{', '}']
        has_code = any(indicator in content for indicator in code_indicators)
        features.append(1 if has_code else 0)
        
        # Nombre de lignes de code estimé
        code_lines = content.count('\n') if has_code else 0
        features.append(code_lines)
        
        # === 2. FEATURES CATÉGORIE ===
        
        try:
            category = Category.objects.get(id=category_id)
            
            # Popularité moyenne de la catégorie (vues)
            category_avg_views = Topic.objects.filter(
                category=category,
                is_active=True
            ).aggregate(avg=Avg('views'))['avg'] or 0
            features.append(category_avg_views)
            
            # Nombre moyen de posts par topic dans cette catégorie
            category_topics = Topic.objects.filter(category=category, is_active=True)
            if category_topics.exists():
                total_posts = sum(t.get_posts_count() for t in category_topics[:50])
                avg_posts = total_posts / min(50, category_topics.count())
                features.append(avg_posts)
            else:
                features.append(0)
            
            # Nombre total de topics dans la catégorie
            features.append(category_topics.count())
            
        except Category.DoesNotExist:
            features.extend([0, 0, 0])
        
        # === 3. FEATURES AUTEUR ===
        
        try:
            author = CustomUser.objects.get(id=author_id)
            
            # Nombre de topics créés par l'auteur
            author_topics_count = Topic.objects.filter(author=author, is_active=True).count()
            features.append(author_topics_count)
            
            # Moyenne de vues des topics de l'auteur
            author_avg_views = Topic.objects.filter(
                author=author,
                is_active=True
            ).aggregate(avg=Avg('views'))['avg'] or 0
            features.append(author_avg_views)
            
            # Nombre total de posts de l'auteur
            author_posts_count = Post.objects.filter(author=author, is_active=True).count()
            features.append(author_posts_count)
            
            # Réputation estimée (likes reçus)
            total_likes = sum(
                post.likes_count for post in 
                Post.objects.filter(author=author, is_active=True)[:100]
            )
            features.append(total_likes)
            
            # Est membre staff
            features.append(1 if author.is_staff else 0)
            
        except CustomUser.DoesNotExist:
            features.extend([0, 0, 0, 0, 0])
        
        # === 4. FEATURES TEMPORELLES ===
        
        if created_at is None:
            created_at = timezone.now()
        
        # Jour de la semaine (0 = lundi, 6 = dimanche)
        features.append(created_at.weekday())
        
        # Heure de la journée
        features.append(created_at.hour)
        
        # Est un weekend
        features.append(1 if created_at.weekday() >= 5 else 0)
        
        # Est en heures de bureau (9h-17h)
        features.append(1 if 9 <= created_at.hour <= 17 else 0)
        
        # === 5. FEATURES DE TENDANCE ===
        
        # Nombre de topics créés dans les dernières 24h
        recent_topics = Topic.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        features.append(recent_topics)
        
        # Nombre de posts dans les dernières 24h (activité générale)
        recent_posts = Post.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        features.append(recent_posts)
        
        return np.array(features).reshape(1, -1)
    
    def extract_text_embedding(self, title: str, content: str) -> Optional[np.ndarray]:
        """
        Extrait un embedding vectoriel du texte
        """
        if not self.text_encoder:
            return None
        
        text = f"{title} {content}"
        try:
            embedding = self.text_encoder.encode(text)
            return embedding
        except Exception as e:
            print(f"Erreur lors de l'extraction d'embedding: {e}")
            return None
    
    def train_models(self, min_samples: int = 50):
        """
        Entraîne les modèles de prédiction sur les données historiques
        
        Args:
            min_samples: Nombre minimum de topics requis pour l'entraînement
        """
        if not SKLEARN_AVAILABLE:
            print("❌ scikit-learn requis pour l'entraînement")
            return False
        
        from forum.models import Topic
        
        # Récupérer tous les topics actifs
        topics = Topic.objects.filter(is_active=True).select_related('author', 'category')
        
        if topics.count() < min_samples:
            print(f"⚠️ Pas assez de données ({topics.count()} topics, {min_samples} requis)")
            return False
        
        print(f"📊 Entraînement sur {topics.count()} topics...")
        
        # Préparer les données
        X = []
        y_views = []
        y_posts = []
        
        for topic in topics:
            features = self.extract_features(
                title=topic.title,
                content=topic.first_post.content if topic.first_post else "",
                category_id=topic.category_id,
                author_id=topic.author_id,
                created_at=topic.created_at
            )
            
            X.append(features.flatten())
            y_views.append(topic.views)
            y_posts.append(topic.get_posts_count())
        
        X = np.array(X)
        y_views = np.array(y_views)
        y_posts = np.array(y_posts)
        
        # Normaliser les features
        X_scaled = self.scaler.fit_transform(X)
        
        # === ENTRAÎNER MODÈLE DE PRÉDICTION DES VUES ===
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_views, test_size=0.2, random_state=42
        )
        
        self.model_views = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.model_views.fit(X_train, y_train)
        
        # Évaluer
        y_pred = self.model_views.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"✅ Modèle VUES - MAE: {mae:.2f}, R²: {r2:.3f}")
        
        # === ENTRAÎNER MODÈLE DE PRÉDICTION DES POSTS ===
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_posts, test_size=0.2, random_state=42
        )
        
        self.model_posts = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.model_posts.fit(X_train, y_train)
        
        # Évaluer
        y_pred = self.model_posts.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"✅ Modèle POSTS - MAE: {mae:.2f}, R²: {r2:.3f}")
        
        # Sauvegarder les modèles
        self.save_models()
        
        return True
    
    def predict(self, title: str, content: str, category_id: int, 
                author_id: int) -> Dict[str, Any]:
        """
        Prédit la popularité d'un topic
        
        Returns:
            Dict avec prédictions et niveau de confiance
        """
        # Vérifier si les modèles sont disponibles
        if self.model_views is None or self.model_posts is None:
            return self._fallback_prediction(title, content, category_id)
        
        try:
            # Extraire les features
            features = self.extract_features(title, content, category_id, author_id)
            features_scaled = self.scaler.transform(features)
            
            # Prédictions
            predicted_views = max(0, int(self.model_views.predict(features_scaled)[0]))
            predicted_posts = max(0, int(self.model_posts.predict(features_scaled)[0]))
            
            # Calculer un score de popularité (0-100)
            popularity_score = min(100, (predicted_views / 10) + (predicted_posts * 5))
            
            # Déterminer la catégorie de popularité
            if popularity_score >= 80:
                category = "Très populaire 🔥"
                confidence = "Haute"
            elif popularity_score >= 60:
                category = "Populaire ⭐"
                confidence = "Moyenne-Haute"
            elif popularity_score >= 40:
                category = "Modéré 📊"
                confidence = "Moyenne"
            elif popularity_score >= 20:
                category = "Faible 📉"
                confidence = "Moyenne-Faible"
            else:
                category = "Très faible 💤"
                confidence = "Faible"
            
            return {
                'predicted_views': predicted_views,
                'predicted_posts': predicted_posts,
                'popularity_score': round(popularity_score, 1),
                'category': category,
                'confidence': confidence,
                'recommendations': self._generate_recommendations(
                    title, content, predicted_views, predicted_posts
                ),
                'method': 'ml_model'
            }
            
        except Exception as e:
            print(f"Erreur lors de la prédiction: {e}")
            return self._fallback_prediction(title, content, category_id)
    
    def _fallback_prediction(self, title: str, content: str, category_id: int) -> Dict[str, Any]:
        """
        Prédiction basique basée sur des heuristiques si le ML n'est pas disponible
        """
        from forum.models import Topic, Category
        
        score = 50  # Score de base
        
        # Ajustements basés sur le titre
        if '?' in title:
            score += 10  # Les questions attirent plus de réponses
        
        if len(title) > 50:
            score -= 5  # Titres trop longs moins attractifs
        elif len(title) < 20:
            score -= 5  # Titres trop courts aussi
        
        # Ajustements basés sur le contenu
        content_length = len(content)
        if 100 < content_length < 500:
            score += 10  # Longueur idéale
        elif content_length > 1000:
            score -= 5  # Trop long
        
        # Code présent
        if '```' in content or 'def ' in content:
            score += 15  # Le code attire l'attention
        
        # Catégorie populaire
        try:
            category = Category.objects.get(id=category_id)
            avg_views = Topic.objects.filter(
                category=category, is_active=True
            ).aggregate(avg=Avg('views'))['avg'] or 0
            
            if avg_views > 100:
                score += 10
            elif avg_views < 20:
                score -= 10
        except:
            pass
        
        # Limiter le score
        score = max(0, min(100, score))
        
        # Estimation basique
        estimated_views = int(score * 2)
        estimated_posts = int(score / 10)
        
        if score >= 70:
            category = "Populaire ⭐"
        elif score >= 40:
            category = "Modéré 📊"
        else:
            category = "Faible 📉"
        
        return {
            'predicted_views': estimated_views,
            'predicted_posts': estimated_posts,
            'popularity_score': score,
            'category': category,
            'confidence': 'Estimation heuristique',
            'recommendations': self._generate_recommendations(
                title, content, estimated_views, estimated_posts
            ),
            'method': 'heuristic'
        }
    
    def _generate_recommendations(self, title: str, content: str, 
                                  views: int, posts: int) -> list:
        """
        Génère des recommandations pour améliorer la popularité
        """
        recommendations = []
        
        # Titre
        if len(title) < 20:
            recommendations.append("📝 Titre trop court - Soyez plus descriptif")
        elif len(title) > 80:
            recommendations.append("✂️ Titre trop long - Soyez plus concis")
        
        if '?' not in title and '?' not in content:
            recommendations.append("❓ Formulez clairement votre question dans le titre")
        
        # Contenu
        if len(content) < 50:
            recommendations.append("📄 Ajoutez plus de détails pour obtenir de meilleures réponses")
        
        if '```' not in content and ('code' in content.lower() or 'erreur' in content.lower()):
            recommendations.append("💻 Incluez des exemples de code pour faciliter l'aide")
        
        # Prédictions
        if views < 20:
            recommendations.append("🎯 Choisissez une catégorie plus active ou reformulez le titre")
        
        if posts < 2:
            recommendations.append("💬 Posez une question spécifique pour encourager les réponses")
        
        if not recommendations:
            recommendations.append("✅ Votre topic est bien structuré !")
        
        return recommendations
    
    def save_models(self):
        """Sauvegarde les modèles entraînés"""
        if self.model_views and self.model_posts:
            try:
                with open(os.path.join(self.models_dir, 'model_views.pkl'), 'wb') as f:
                    pickle.dump(self.model_views, f)
                
                with open(os.path.join(self.models_dir, 'model_posts.pkl'), 'wb') as f:
                    pickle.dump(self.model_posts, f)
                
                with open(os.path.join(self.models_dir, 'scaler.pkl'), 'wb') as f:
                    pickle.dump(self.scaler, f)
                
                print("✅ Modèles sauvegardés avec succès")
            except Exception as e:
                print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def load_models(self):
        """Charge les modèles entraînés s'ils existent"""
        try:
            views_path = os.path.join(self.models_dir, 'model_views.pkl')
            posts_path = os.path.join(self.models_dir, 'model_posts.pkl')
            scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
            
            if os.path.exists(views_path) and os.path.exists(posts_path):
                with open(views_path, 'rb') as f:
                    self.model_views = pickle.load(f)
                
                with open(posts_path, 'rb') as f:
                    self.model_posts = pickle.load(f)
                
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                print("✅ Modèles chargés avec succès")
        except Exception as e:
            print(f"⚠️ Impossible de charger les modèles: {e}")
    
    def analyze_topic_performance(self, topic_id: int) -> Dict[str, Any]:
        """
        Analyse la performance réelle vs prédite d'un topic
        """
        from forum.models import Topic
        
        try:
            topic = Topic.objects.get(id=topic_id, is_active=True)
            
            # Prédiction actuelle
            prediction = self.predict(
                title=topic.title,
                content=topic.first_post.content if topic.first_post else "",
                category_id=topic.category_id,
                author_id=topic.author_id
            )
            
            # Performance réelle
            actual_views = topic.views
            actual_posts = topic.get_posts_count()
            
            # Comparaison
            views_diff = actual_views - prediction['predicted_views']
            posts_diff = actual_posts - prediction['predicted_posts']
            
            # Performance relative
            if actual_views > prediction['predicted_views'] * 1.5:
                performance = "🚀 Surperformance"
            elif actual_views < prediction['predicted_views'] * 0.5:
                performance = "📉 Sous-performance"
            else:
                performance = "✅ Conforme aux attentes"
            
            return {
                'topic_id': topic_id,
                'topic_title': topic.title,
                'predicted_views': prediction['predicted_views'],
                'actual_views': actual_views,
                'views_difference': views_diff,
                'predicted_posts': prediction['predicted_posts'],
                'actual_posts': actual_posts,
                'posts_difference': posts_diff,
                'performance': performance,
                'created_days_ago': (timezone.now() - topic.created_at).days
            }
            
        except Topic.DoesNotExist:
            return {'error': 'Topic non trouvé'}


# Instance globale (singleton)
_predictor_instance = None

def get_predictor() -> PopularityPredictor:
    """Retourne l'instance singleton du prédicteur"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = PopularityPredictor()
    return _predictor_instance


# === FONCTIONS UTILITAIRES ===

def predict_topic_popularity(title: str, content: str, category_id: int, 
                            author_id: int) -> Dict[str, Any]:
    """
    Fonction wrapper simple pour prédire la popularité
    """
    predictor = get_predictor()
    return predictor.predict(title, content, category_id, author_id)


def train_popularity_models():
    """
    Entraîne les modèles de prédiction (à exécuter périodiquement)
    """
    predictor = get_predictor()
    return predictor.train_models()


def get_trending_topics(limit: int = 10) -> list:
    """
    Retourne les topics qui dépassent les prédictions (trending)
    """
    from forum.models import Topic
    
    predictor = get_predictor()
    recent_topics = Topic.objects.filter(
        is_active=True,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('author', 'category')
    
    trending = []
    
    for topic in recent_topics:
        analysis = predictor.analyze_topic_performance(topic.id)
        if 'error' not in analysis:
            if analysis['actual_views'] > analysis['predicted_views'] * 1.5:
                trending.append({
                    'topic': topic,
                    'overperformance': analysis['views_difference'],
                    'score': analysis['actual_views'] / max(1, analysis['predicted_views'])
                })
    
    # Trier par score
    trending.sort(key=lambda x: x['score'], reverse=True)
    
    return trending[:limit]


# ========================================
# SYSTÈME DE POPULARITÉ TEMPS RÉEL
# ========================================

class TopicPopularityPredictor:
    """
    Système de scoring de popularité en temps réel
    Combine algorithme heuristique + ML
    """
    
    MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml_models', 'topic_popularity_model.pkl')
    
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Charge le modèle ML s'il existe"""
        if os.path.exists(self.MODEL_PATH):
            try:
                import joblib
                self.model = joblib.load(self.MODEL_PATH)
                print(f"✓ Modèle chargé: {self.MODEL_PATH}")
            except Exception as e:
                print(f"⚠ Erreur chargement modèle: {e}")
                self.model = None
    
    def calculate_realtime_score(self, topic):
        """Score basé sur l'activité actuelle"""
        from .models import Post
        
        now = timezone.now()
        age_hours = (now - topic.created_at).total_seconds() / 3600
        age_factor = 1.0 / (age_hours + 1.0)
        
        # Métriques
        posts_count = topic.posts.filter(is_active=True).count()
        likes_count = sum([p.likes.count() for p in topic.posts.filter(is_active=True)])
        
        # Activité récente (24h)
        last_24h = now - timedelta(hours=24)
        recent_posts = topic.posts.filter(created_at__gte=last_24h, is_active=True).count()
        
        # Calcul du score
        score = (
            min(topic.views / 100.0, 5.0) +
            min(posts_count / 10.0, 5.0) * 2.0 +
            min(likes_count / 5.0, 5.0) * 1.5 +
            min(recent_posts * 2.0, 10.0) * 3.0 +
            (10.0 if topic.status == 'pinned' else 0.0)
        )
        
        return score * age_factor * 2.0
    
    def extract_features(self, topic):
        """Features pour ML"""
        from .models import Post
        
        now = timezone.now()
        age_hours = (now - topic.created_at).total_seconds() / 3600
        
        posts_count = topic.posts.filter(is_active=True).count()
        likes_count = sum([p.likes.count() for p in topic.posts.filter(is_active=True)])
        
        # Activité temporelle
        h6 = now - timedelta(hours=6)
        h24 = now - timedelta(hours=24)
        h48 = now - timedelta(hours=48)
        
        return {
            'topic_age_hours': age_hours,
            'hours_since_update': (now - topic.updated_at).total_seconds() / 3600,
            'views': topic.views,
            'posts_count': posts_count,
            'likes_count': likes_count,
            'posts_last_6h': topic.posts.filter(created_at__gte=h6, is_active=True).count(),
            'posts_last_24h': topic.posts.filter(created_at__gte=h24, is_active=True).count(),
            'posts_last_48h': topic.posts.filter(created_at__gte=h48, is_active=True).count(),
            'posts_per_hour': posts_count / max(age_hours, 1.0),
            'author_reputation': topic.author.topics.count() + topic.author.posts.count(),
            'category_size': topic.category.topics.filter(is_active=True).count(),
            'is_pinned': 1 if topic.status == 'pinned' else 0,
            'has_solution': 1 if topic.posts.filter(is_solution=True).exists() else 0,
        }
    
    def predict_ml_score(self, topic):
        """Prédiction ML si modèle disponible"""
        if not self.model:
            return 0.0
        
        try:
            import pandas as pd
            features = self.extract_features(topic)
            df = pd.DataFrame([features])
            
            if hasattr(self.model, 'feature_names_in_'):
                df = df[self.model.feature_names_in_]
            
            return max(0.0, float(self.model.predict(df)[0]))
        except:
            return 0.0
    
    def calculate_popularity_score(self, topic):
        """Score final combiné"""
        realtime = self.calculate_realtime_score(topic)
        ml = self.predict_ml_score(topic)
        
        if self.model:
            return 0.3 * realtime + 0.7 * ml
        return realtime
    
    def update_topic_popularity(self, topic):
        """Met à jour le score du topic"""
        score = self.calculate_popularity_score(topic)
        topic.popularity_score = score
        topic.popularity_refreshed_at = timezone.now()
        topic.save(update_fields=['popularity_score', 'popularity_refreshed_at'])
        return score


def get_popular_topics(category=None, limit=5, hours=48):
    """Retourne les topics populaires"""
    from .models import Topic
    
    cutoff = timezone.now() - timedelta(hours=hours)
    qs = Topic.objects.filter(
        is_active=True,
        created_at__gte=cutoff
    ).select_related('author', 'category')
    
    if category:
        qs = qs.filter(category=category)
    
    return qs.order_by('-popularity_score', '-views')[:limit]


def get_trending_topics_simple(category=None, limit=5):
    """Topics en tendance (activité récente)"""
    from .models import Topic
    
    last_24h = timezone.now() - timedelta(hours=24)
    qs = Topic.objects.filter(
        is_active=True,
        updated_at__gte=last_24h
    ).select_related('author', 'category')
    
    if category:
        qs = qs.filter(category=category)
    
    return qs.order_by('-popularity_score', '-updated_at')[:limit]

