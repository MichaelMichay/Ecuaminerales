from django.urls import path

from . import views_panel as v

app_name = 'publico_panel'

urlpatterns = [
    path('comunicados/', v.comunicados, name='comunicados'),
    path('comunicados/nuevo/', v.comunicado_crear, name='comunicado_crear'),
    path('comunicados/<int:pk>/editar/', v.comunicado_editar, name='comunicado_editar'),
    path('comunicados/<int:pk>/eliminar/', v.comunicado_eliminar, name='comunicado_eliminar'),
    path('categorias/', v.categorias, name='categorias'),
    path('categorias/<int:pk>/editar/', v.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/alternar/<str:campo>/', v.categoria_alternar, name='categoria_alternar'),
    path('imagenes/', v.insumos_imagenes, name='imagenes'),
    path('imagenes/<int:pk>/', v.insumo_imagen, name='insumo_imagen'),
    path('documentos/', v.documentos, name='documentos'),
    path('documentos/nuevo/', v.documento_crear, name='documento_crear'),
    path('documentos/<int:pk>/editar/', v.documento_editar, name='documento_editar'),
    path('documentos/<int:pk>/eliminar/', v.documento_eliminar, name='documento_eliminar'),
    path('documentos/<int:pk>/ver/', v.documento_vista, name='documento_vista'),

]