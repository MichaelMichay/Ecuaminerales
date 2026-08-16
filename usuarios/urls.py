from django.urls import path
from .import views
from django.contrib.auth import logout

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('usuarios/', views.lista_usuarios, name='usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('roles/', views.lista_roles, name='roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('roles/editar/<int:id>/', views.editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:id>/', views.eliminar_rol, name='eliminar_rol'),
    path('notificaciones/leidas/', views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),
    path('notificaciones/leida/<int:id>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path(
    'usuarios/restablecer-password/<int:id>/',
    views.restablecer_password_usuario,
    name='restablecer_password_usuario'
),
    ]