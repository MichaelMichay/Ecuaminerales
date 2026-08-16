from django.urls import path
from . import views

urlpatterns = [
    path('auditoria/', views.lista_auditoria, name='auditoria'),
    path('auditoria/pdf/', views.reporte_auditoria_pdf, name='reporte_auditoria_pdf'),
    path('trazabilidad/', views.trazabilidad_operacional, name='trazabilidad_operacional'),
    path('trazabilidad/pdf/', views.trazabilidad_pdf, name='trazabilidad_pdf'),
    path('trazabilidad/excel/', views.trazabilidad_excel, name='trazabilidad_excel'),
]