from django.urls import path
from . import views

app_name = 'template_back'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Gestion des catégories du forum
    path('forum/categories/', views.forum_categories_list, name='forum_categories_list'),
    path('forum/categories/create/', views.forum_category_create, name='forum_category_create'),
    path('forum/categories/<int:pk>/edit/', views.forum_category_edit, name='forum_category_edit'),
    path('forum/categories/<int:pk>/delete/', views.forum_category_delete, name='forum_category_delete'),
    path('forum/categories/<int:pk>/toggle/', views.forum_category_toggle_active, name='forum_category_toggle_active'),
]
