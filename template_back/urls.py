from django.urls import path
from . import views

app_name = 'template_back'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
