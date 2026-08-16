from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_insumos, name='inventario'),
    path('crear/', views.crear_insumo, name='crear_insumo'),
      path('editar/<int:id>/', views.editar_insumo, name='editar_insumo'),
    path('eliminar/<int:id>/', views.eliminar_insumo, name='eliminar_insumo'),
    path('reporte/pdf/', views.reporte_inventario_pdf, name='reporte_inventario_pdf'),
    path('categorias/', views.lista_categorias, name='categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('lugares/', views.lista_lugares, name='lugares'),
    path('lugares/crear/', views.crear_lugar, name='crear_lugar'),
    path('categorias/editar/<int:id>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:id>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('lugares/editar/<int:id>/', views.editar_lugar, name='editar_lugar'),
    path('lugares/eliminar/<int:id>/', views.eliminar_lugar, name='eliminar_lugar'),
    path('kardex/', views.kardex_inventario, name='kardex_inventario'),
    path('kardex/pdf/', views.kardex_pdf, name='kardex_pdf'),
    path('kardex/excel/', views.kardex_excel, name='kardex_excel'),
]