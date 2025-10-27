from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profil et dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:pk>/', views.profile_view, name='profile_detail'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('password/change/', views.change_password_view, name='change_password'),
    
    # Gestion des utilisateurs
    path('users/', views.users_list_view, name='users_list'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
    
    # AJAX endpoints
    path('ajax/check-username/', views.ajax_check_username, name='ajax_check_username'),
    path('ajax/check-email/', views.ajax_check_email, name='ajax_check_email'),
]
