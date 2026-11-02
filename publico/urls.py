from django.urls import path
from . import views

app_name = 'publico'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('comunicado/<int:pk>/', views.comunicado, name='comunicado'),
    path('documentos/<int:pk>/ver/', views.documento_ver, name='documento_ver'),
    path('documentos/<int:pk>/descargar/', views.documento_descargar, name='documento_descargar'),
]