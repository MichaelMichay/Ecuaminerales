from django.urls import path
from . import views

app_name = 'publico'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('comunicado/<int:pk>/', views.comunicado, name='comunicado'),
]
