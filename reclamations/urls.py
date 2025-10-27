# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'reclamations'

urlpatterns = [
    # URLs utilisateur
    path('', views.reclamation_list, name='list'),
    path('create/', views.reclamation_create, name='create'),
    path('<int:pk>/', views.reclamation_detail, name='detail'),
    path('reponses-lues/', views.reponses_lues_list, name='reponses_lues'),
    
    # URLs administrateur
    path('admin/', views.admin_reclamation_list, name='admin_list'),
    path('<int:pk>/edit/', views.reclamation_edit, name='edit'),
    
    # URLs enseignant
    path('assignees/', views.reclamations_assignees, name='assignees'),
    
    # URLs réponses administrateur
    path('<int:pk>/admin-response/create/', views.admin_response_create, name='admin_response_create'),
    path('<int:pk>/admin-response/<int:response_pk>/edit/', views.admin_response_edit, name='admin_response_edit'),
    path('<int:pk>/admin-response/<int:response_pk>/delete/', views.admin_response_delete, name='admin_response_delete'),
    
    # URLs AJAX
    path('<int:pk>/assign/', views.reclamation_assign, name='assign'),
    path('<int:pk>/change-status/', views.reclamation_change_status, name='change_status'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
]
