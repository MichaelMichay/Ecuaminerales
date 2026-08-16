from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_ordenes, name='ordenes'),
    path('crear/', views.crear_orden, name='crear_orden'),
    path('despachar/<int:id>/', views.despachar_orden, name='despachar_orden'),
    path('historial/', views.lista_despachos, name='despachos'),
    path('reporte/pdf/', views.reporte_ordenes_pdf, name='reporte_ordenes_pdf'),
    path('despachos/reporte/pdf/', views.reporte_despachos_pdf, name='reporte_despachos_pdf'),
    path('panel-bodeguero/', views.panel_bodeguero, name='panel_bodeguero'),
    path('panel-bodeguero/aprobar/<int:id>/',views.aprobar_orden_bodeguero, name='aprobar_orden_bodeguero'),
    path( 'panel-bodeguero/rechazar/<int:id>/', views.rechazar_orden_bodeguero,name='rechazar_orden_bodeguero'),
    path('despacho/<int:id>/detalle/', views.detalle_despacho,name='detalle_despacho'),
    path('despacho/<int:id>/pdf/',views.comprobante_despacho_pdf, name='comprobante_despacho_pdf'),
    path('bodeguero/ordenes/', views.ordenes_bodeguero, name='ordenes_bodeguero'),
    path('bodeguero/historial/', views.historial_bodeguero, name='historial_bodeguero'),
    path('perforista/', views.panel_perforista, name='panel_perforista'),
    path('perforista/mis-ordenes/', views.mis_ordenes_perforista, name='mis_ordenes_perforista'),
    path('editar-materiales/<int:orden_id>/', views.editar_materiales, name='editar_materiales'),
]