from reportes.models import Notificacion


def notificaciones(request):
    if request.user.is_authenticated:
        notificaciones_recientes = Notificacion.objects.filter(
            usuario=request.user
        ).order_by('-fecha')[:5]

        total_notificaciones = Notificacion.objects.filter(
            usuario=request.user,
            estado=False
        ).count()

        return {
            'total_notificaciones': total_notificaciones,
            'notificaciones_recientes': notificaciones_recientes
        }

    return {
        'total_notificaciones': 0,
        'notificaciones_recientes': []
    }