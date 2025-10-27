from django.urls import path
from . import views

app_name = 'cours'

urlpatterns = [
    # Vue administrative
    path('admin/courses/', views.admin_course_list, name='admin_course_list'),

    # Pages principales
    path('', views.course_list, name='course_list'),
    path('subjects/', views.subject_list, name='subject_list'),

    # Création de cours (enseignants) - doit venir avant les patterns génériques
    path('create/', views.course_create, name='course_create'),

    # Gestion du contenu (enseignants)
    path('<slug:slug>/module/create/', views.course_module_create, name='course_module_create'),
    path('<slug:slug>/module/<int:module_id>/edit/', views.course_module_edit, name='course_module_edit'),
    path('<slug:slug>/module/<int:module_id>/delete/', views.course_module_delete, name='course_module_delete'),
    path('<slug:slug>/resource/create/', views.course_resource_create, name='course_resource_create'),
    path('<slug:slug>/resource/<int:resource_id>/edit/', views.course_resource_edit, name='course_resource_edit'),
    path('<slug:slug>/resource/<int:resource_id>/delete/', views.course_resource_delete, name='course_resource_delete'),

    # Détails
    path('subject/<slug:slug>/', views.subject_detail, name='subject_detail'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),

    # Inscription et progression
    path('<slug:slug>/enroll/', views.course_enroll, name='course_enroll'),
    path('<slug:slug>/unenroll/', views.course_unenroll, name='course_unenroll'),
    path('<slug:slug>/progress/', views.course_progress, name='course_progress'),

    # Avis
    path('<slug:slug>/review/', views.course_review, name='course_review'),

    # Suppression de cours (admin et enseignant propriétaire)
    path('<slug:slug>/delete/', views.course_delete, name='course_delete'),

    # API pour AJAX (optionnel)
    path('api/enroll/<int:course_id>/', views.api_enroll_course, name='api_enroll_course'),
    path('api/progress/<int:enrollment_id>/', views.api_update_progress, name='api_update_progress'),
    path('resource/view/<int:resource_id>/', views.view_pdf_resource, name='view_pdf_resource'),

]
