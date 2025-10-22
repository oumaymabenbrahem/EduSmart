from django.urls import path
from . import views

app_name = 'template_front'

urlpatterns = [
    path('', views.index, name='index'),
]
