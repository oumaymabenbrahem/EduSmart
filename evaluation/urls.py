from django.urls import path
from . import views

app_name = 'evaluation'

urlpatterns = [
    path('', views.evaluations_list, name='list'),  # Page par défaut est maintenant la liste unifiée
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_evaluation, name='create'),  # Création d'évaluation

    # URLs pour les étudiants
    path('student/', views.student_evaluations, name='student_list'),
    path('take/<int:evaluation_id>/', views.take_evaluation, name='take_evaluation'),
    path('results/<int:evaluation_id>/', views.evaluation_results, name='results'),
    
    # URLs pour l'administration
    path('admin/list/', views.admin_evaluations_list, name='admin_list'),
    path('admin/details/<int:evaluation_id>/', views.admin_evaluation_details, name='admin_details'),
    path('admin/edit/<int:evaluation_id>/', views.admin_evaluation_edit, name='admin_edit'),
    path('admin/delete/<int:evaluation_id>/', views.admin_evaluation_delete, name='admin_delete'),
    path('admin/toggle-publish/<int:evaluation_id>/', views.admin_evaluation_toggle_publish, name='admin_toggle_publish'),
]
