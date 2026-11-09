
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('', include('publico.urls')),

    path('admin/', admin.site.urls),

    path('inventario/', include('inventario.urls')),
    path('ordenes/', include('despachos.urls')),
    path('reportes/', include('reportes.urls')),
    path('polvorin/', include('polvorin.urls')),

    path('sistema/pagina-publica/', include('publico.urls_panel')),
    path('sistema/', include('usuarios.urls')),
    path('guardias/', include('guardias.urls')),

    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT}
    ),
]
