from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_polvorin, name='panel_polvorin'),
    path('entregar/<int:id>/', views.registrar_entrega_polvorin, name='registrar_entrega_polvorin'),
    path('detalle/<int:id>/', views.detalle_entrega_polvorin, name='detalle_entrega_polvorin'),
    path('despacho/<int:id>/detalle/', views.detalle_despacho_polvorin, name='detalle_despacho_polvorin'),
    path('rechazar/<int:id>/', views.rechazar_entrega_polvorin, name='rechazar_entrega_polvorin'),
    path('historial/', views.historial_polvorin, name='historial_polvorin'),
    path('entrega/<int:id>/pdf/', views.comprobante_entrega_pdf, name='comprobante_entrega_pdf'),
]