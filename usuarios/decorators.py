from django.shortcuts import redirect


def rol_requerido(roles_permitidos):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.rol and request.user.rol.nombre_rol in roles_permitidos:
                    return view_func(request, *args, **kwargs)

            return redirect('dashboard')

        return wrapper

    return decorator