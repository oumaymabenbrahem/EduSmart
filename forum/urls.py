from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import views_ai_predictions
from . import views_category_predictions

app_name = 'forum'

urlpatterns = [
    # Pages principales
    path('', views.forum_index, name='index'),
    path('search/', views.search, name='search'),
    
    # Redirection pour l'ancienne URL (compatibilité)
    path('topic/new/', RedirectView.as_view(pattern_name='forum:index', permanent=True)),
    
    # Catégories
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Sujets - URLs spécifiques AVANT les patterns génériques
    path('<slug:category_slug>/nouveau/', views.topic_create, name='topic_create'),
    path('<slug:category_slug>/<slug:topic_slug>/modifier/', views.topic_update, name='topic_update'),
    path('<slug:category_slug>/<slug:topic_slug>/supprimer/', views.topic_delete, name='topic_delete'),
    path('<slug:category_slug>/<slug:topic_slug>/', views.topic_detail, name='topic_detail'),
    
    # Posts
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:pk>/like/', views.post_like, name='post_like'),
    path('post/<int:post_pk>/solution/', views.mark_solution, name='mark_solution'),
    
    # Commentaires
    path('post/<int:post_pk>/comment/', views.comment_create, name='comment_create'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    
    # Signalements
    path('report/', views.report_content, name='report_content'),
    path('reports/', views.reports_list, name='reports_list'),
    
    # Espace utilisateur
    path('my-topics/', views.my_topics, name='my_topics'),
    path('my-posts/', views.my_posts, name='my_posts'),
    
    # ===== PRÉDICTIONS IA TOPICS =====
    path('api/predict-popularity/', views_ai_predictions.predict_topic_api, name='predict_api'),
    path('topic/<int:topic_id>/popularity/', views_ai_predictions.topic_popularity_preview, name='topic_popularity'),
    path('my-topics/predictions/', views_ai_predictions.my_topics_predictions, name='my_topics_predictions'),
    path('admin/trending/', views_ai_predictions.trending_topics_dashboard, name='trending_dashboard'),
    path('admin/popularity-stats/', views_ai_predictions.popularity_stats, name='popularity_stats'),
    
    # ===== PRÉDICTIONS IA CATÉGORIES =====
    path('api/category-popularity/', views_category_predictions.category_popularity_api, name='category_popularity_api'),
    path('api/category-popularity/<int:category_id>/', views_category_predictions.category_popularity_api, name='category_popularity_detail_api'),
    path('api/compare-categories/', views_category_predictions.compare_categories_api, name='compare_categories_api'),
    path('admin/categories-dashboard/', views_category_predictions.categories_dashboard, name='categories_dashboard'),
    path('admin/trending-categories/', views_category_predictions.trending_categories, name='trending_categories'),
    path('admin/category-stats/', views_category_predictions.category_popularity_stats, name='category_stats'),
    path('recommendations/', views_category_predictions.category_recommendations, name='category_recommendations'),
]
