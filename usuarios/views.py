from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest
from django.db import models
from usuarios.models import Usuario
from inventario.models import Insumo
from despachos.models import OrdenTiro, Despacho
from reportes.models import Notificacion
from .forms import UsuarioForm, RolForm, UsuarioEditarForm, PerfilUsuarioForm
from .models import Rol
from django.core.paginator import Paginator
from django.contrib import messages
from .decorators import rol_requerido
from reportes.models import Auditoria
from django import forms
from django.core.exceptions import ValidationError
import re
from .forms import UsuarioForm, RolForm, UsuarioEditarForm, PerfilUsuarioForm, CambiarPasswordForm
from django.contrib.auth import update_session_auth_hash
def login_view(request: HttpRequest):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)
            if user.rol.nombre_rol == 'Administrador':
                return redirect('dashboard')

            elif user.rol.nombre_rol == 'Bodeguero':
                return redirect('panel_bodeguero')

            elif user.rol.nombre_rol == 'Perforista':
                return redirect('panel_perforista')

            elif user.rol.nombre_rol == 'Polvorinero':
                return redirect('panel_polvorin')

            return redirect('dashboard')
        else:

            messages.error(
                request,
                'Usuario o contraseña incorrectos.'
            )

    return render(request, 'login.html')

@login_required
def dashboard(request: HttpRequest):

    total_usuarios = Usuario.objects.count()
    total_insumos = Insumo.objects.count()
    total_ordenes = OrdenTiro.objects.count()
    total_despachos = Despacho.objects.count()

    ordenes_pendientes = OrdenTiro.objects.filter(
        estado='PENDIENTE'
    ).count()

    ordenes_despachadas = OrdenTiro.objects.filter(
        estado='DESPACHADA'
    ).count()

    ordenes_rechazadas = OrdenTiro.objects.filter(
        estado='RECHAZADA'
    ).count()

    stock_bajo = Insumo.objects.filter(
        stock__lte=models.F('stock_minimo')
    ).count()

    ultimas_ordenes = OrdenTiro.objects.all().order_by(
        '-fecha_orden'
    )[:5]

    ultimos_despachos = Despacho.objects.all().order_by(
        '-fecha_despacho'
    )[:5]

    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    ).order_by('-fecha')[:5]

    total_notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        estado=False
    ).count()

    tiempos_despacho = []
    tiempos_entrega = []

    for orden in OrdenTiro.objects.all():

        despacho = Despacho.objects.filter(
            orden_tiro=orden
        ).first()

        if despacho:

            diferencia = despacho.fecha_despacho - orden.fecha_orden

            tiempos_despacho.append(
                diferencia.total_seconds() / 60
            )

            try:
                entrega = despacho.entregapolvorin

                diferencia_entrega = (
                    entrega.fecha_entrega -
                    despacho.fecha_despacho
                )

                tiempos_entrega.append(
                    diferencia_entrega.total_seconds() / 60
                )

            except:
                pass

    promedio_despacho = 0
    promedio_entrega = 0

    if tiempos_despacho:
        promedio_despacho = round(
            sum(tiempos_despacho) / len(tiempos_despacho),
            2
        )

    if tiempos_entrega:
        promedio_entrega = round(
            sum(tiempos_entrega) / len(tiempos_entrega),
            2
        )

    context = {
        'total_usuarios': total_usuarios,
        'total_insumos': total_insumos,
        'total_ordenes': total_ordenes,
        'total_despachos': total_despachos,

        'ordenes_pendientes': ordenes_pendientes,
        'ordenes_despachadas': ordenes_despachadas,
        'ordenes_rechazadas': ordenes_rechazadas,

        'stock_bajo': stock_bajo,

        'promedio_despacho': promedio_despacho,
        'promedio_entrega': promedio_entrega,

        'ultimas_ordenes': ultimas_ordenes,
        'ultimos_despachos': ultimos_despachos,

        'notificaciones': notificaciones,
        'total_notificaciones': total_notificaciones,
    }

    return render(request, 'dashboard.html', context)

def logout_view(request: HttpRequest):
    logout(request)
    return redirect('login')

@login_required
def lista_usuarios(request):
    buscar = request.GET.get('buscar')

    usuarios = Usuario.objects.all().order_by('username')

    if buscar:
        usuarios = usuarios.filter(username__icontains=buscar)

    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'usuarios/lista_usuarios.html', {
        'usuarios': usuarios,
        'buscar': buscar,
        'page_obj': usuarios
    })
@login_required
@rol_requerido(['Administrador'])
def crear_usuario(request):

    if request.method == 'POST':

        form = UsuarioForm(request.POST)

        if form.is_valid():

            usuario = form.save(commit=False)

            password = form.cleaned_data['password']
            usuario.set_password(password)
            usuario.save()

            Auditoria.objects.create(
                usuario=request.user,
                accion='CREACIÓN DE USUARIO',
                descripcion=(
                    f'El administrador {request.user.username} creó el usuario '
                    f'{usuario.username} con rol {usuario.rol.nombre_rol}.'
                )
            )

            messages.success(
                request,
                'Usuario creado correctamente.'
            )

            return redirect('usuarios')

        else:

            messages.error(
                request,
                'No se pudo crear el usuario. Revisa los datos.'
            )

    else:

        form = UsuarioForm()

    return render(request, 'usuarios/crear_usuario.html', {
        'form': form
    })
@login_required
@rol_requerido(['Administrador'])
def editar_usuario(request, id):

    usuario = Usuario.objects.get(id=id)

    if request.method == 'POST':

        rol_anterior = usuario.rol.nombre_rol if usuario.rol else 'Sin rol'
        estado_anterior = 'Activo' if usuario.estado else 'Inactivo'
        correo_anterior = usuario.email
        telefono_anterior = usuario.telefono

        form = UsuarioEditarForm(request.POST, instance=usuario)

        if form.is_valid():

            usuario_editado = form.save(commit=False)

            nueva_password = form.cleaned_data.get('nueva_password')

            password_actualizada = False

            if nueva_password:
                usuario_editado.set_password(nueva_password)
                password_actualizada = True

            usuario_editado.save()

            rol_nuevo = usuario_editado.rol.nombre_rol if usuario_editado.rol else 'Sin rol'
            estado_nuevo = 'Activo' if usuario_editado.estado else 'Inactivo'

            cambios = []

            if correo_anterior != usuario_editado.email:
                cambios.append(
                    f'correo: {correo_anterior} → {usuario_editado.email}'
                )

            if telefono_anterior != usuario_editado.telefono:
                cambios.append(
                    f'teléfono: {telefono_anterior} → {usuario_editado.telefono}'
                )

            if rol_anterior != rol_nuevo:
                cambios.append(
                    f'rol: {rol_anterior} → {rol_nuevo}'
                )

            if estado_anterior != estado_nuevo:
                cambios.append(
                    f'estado: {estado_anterior} → {estado_nuevo}'
                )

            if password_actualizada:
                cambios.append(
                    'contraseña actualizada por el administrador'
                )

            if cambios:
                descripcion_cambios = '; '.join(cambios)
            else:
                descripcion_cambios = 'No se detectaron cambios en los datos permitidos.'

            Auditoria.objects.create(
                usuario=request.user,
                accion='EDICIÓN DE USUARIO',
                descripcion=(
                    f'El administrador {request.user.username} modificó el usuario '
                    f'{usuario_editado.username}. Cambios: {descripcion_cambios}.'
                )
            )

            if password_actualizada:
                Auditoria.objects.create(
                    usuario=request.user,
                    accion='REINICIO DE CONTRASEÑA',
                    descripcion=(
                        f'El administrador {request.user.username} actualizó '
                        f'la contraseña del usuario {usuario_editado.username}.'
                    )
                )

            messages.success(
                request,
                'Usuario actualizado correctamente.'
            )

            return redirect('usuarios')

        else:

            messages.error(
                request,
                'No se pudo actualizar el usuario. Revisa los datos.'
            )

    else:

        form = UsuarioEditarForm(instance=usuario)

    return render(request, 'usuarios/editar_usuario.html', {
        'form': form,
        'usuario': usuario
    })
@login_required
def mi_perfil(request):

    usuario = request.user

    username_anterior = usuario.username
    correo_anterior = usuario.email
    telefono_anterior = usuario.telefono

    if request.method == 'POST':

        form = PerfilUsuarioForm(request.POST, instance=usuario)

        if form.is_valid():

            usuario_editado = form.save(commit=False)

            nueva_password = form.cleaned_data.get('nueva_password')

            password_actualizada = False

            if nueva_password:
                usuario_editado.set_password(nueva_password)
                password_actualizada = True

            usuario_editado.save()

            if password_actualizada:
                update_session_auth_hash(request, usuario_editado)

            cambios = []

            if username_anterior != usuario_editado.username:
                cambios.append(
                    f'usuario: {username_anterior} → {usuario_editado.username}'
                )

            if correo_anterior != usuario_editado.email:
                cambios.append(
                    f'correo: {correo_anterior} → {usuario_editado.email}'
                )

            if telefono_anterior != usuario_editado.telefono:
                cambios.append(
                    f'teléfono: {telefono_anterior} → {usuario_editado.telefono}'
                )

            if password_actualizada:
                cambios.append(
                    'contraseña actualizada'
                )

            if cambios:
                descripcion_cambios = '; '.join(cambios)
            else:
                descripcion_cambios = 'No se detectaron cambios.'

            Auditoria.objects.create(
                usuario=request.user,
                accion='ACTUALIZACIÓN DE PERFIL',
                descripcion=(
                    f'El usuario {username_anterior} actualizó su perfil. '
                    f'Cambios: {descripcion_cambios}.'
                )
            )

            if password_actualizada:
                Auditoria.objects.create(
                    usuario=request.user,
                    accion='CAMBIO DE CONTRASEÑA',
                    descripcion=(
                        f'El usuario {username_anterior} cambió su propia contraseña.'
                    )
                )

            messages.success(
                request,
                'Perfil actualizado correctamente.'
            )

            return redirect('mi_perfil')

        else:

            messages.error(
                request,
                'No se pudo actualizar el perfil. Revisa los datos.'
            )

    else:

        form = PerfilUsuarioForm(instance=usuario)

    return render(request, 'usuarios/mi_perfil.html', {
        'form': form,
        'usuario': usuario
    })


@login_required
@rol_requerido(['Administrador'])
def eliminar_usuario(request, id):

    usuario = Usuario.objects.get(id=id)

    username = usuario.username
    rol = usuario.rol.nombre_rol if usuario.rol else 'Sin rol'
    correo = usuario.email

    usuario.delete()

    Auditoria.objects.create(
        usuario=request.user,
        accion='ELIMINACIÓN DE USUARIO',
        descripcion=(
            f'El administrador {request.user.username} eliminó el usuario '
            f'{username} con rol {rol} y correo {correo}.'
        )
    )

    messages.success(
        request,
        'Usuario eliminado correctamente.'
    )

    return redirect('usuarios')
@login_required
def lista_roles(request):
    roles = Rol.objects.all().order_by('nombre_rol')

    paginator = Paginator(roles, 10)
    page_number = request.GET.get('page')
    roles = paginator.get_page(page_number)

    return render(request, 'usuarios/lista_roles.html', {
        'roles': roles,
        'page_obj': roles
    })

@login_required
def crear_rol(request):

    if request.method == 'POST':

        form = RolForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request, 'Rol creado correctamente.')

            return redirect('roles')

        else:

            messages.error(request, 'No se pudo crear el rol.')

    else:

        form = RolForm()

    return render(request, 'usuarios/crear_rol.html', {
        'form': form
    })


@login_required
def editar_rol(request, id):

    rol = Rol.objects.get(id=id)

    if request.method == 'POST':

        form = RolForm(request.POST, instance=rol)

        if form.is_valid():

            form.save()

            messages.success(request, 'Rol actualizado correctamente.')

            return redirect('roles')

        else:

            messages.error(request, 'No se pudo actualizar el rol.')

    else:

        form = RolForm(instance=rol)

    return render(request, 'usuarios/editar_rol.html', {
        'form': form,
        'rol': rol
    })

@login_required
def eliminar_rol(request, id):

    rol = Rol.objects.get(id=id)

    rol.delete()

    messages.success(request, 'Rol eliminado correctamente.')

    return redirect('roles')

@login_required
def marcar_notificaciones_leidas(request):
    Notificacion.objects.filter(
        usuario=request.user,
        estado=False
    ).update(estado=True)

    return redirect('dashboard')

@login_required
def marcar_notificacion_leida(request, id):
    notificacion = Notificacion.objects.get(
        id=id,
        usuario=request.user
    )

    notificacion.estado = True
    notificacion.save()

    return redirect('dashboard')



class PerfilUsuarioForm(forms.ModelForm):

    nueva_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Opcional'
        }),
        label='Nueva contraseña'
    )

    class Meta:
        model = Usuario

        fields = [
            'email',
            'telefono',
        ]

        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']

        if not re.match(r'^09\d{8}$', telefono):
            raise ValidationError(
                'El número debe iniciar con 09 y tener 10 dígitos.'
            )

        return telefono

    def clean_nueva_password(self):
        password = self.cleaned_data.get('nueva_password')

        if password and len(password) < 8:
            raise ValidationError(
                'La contraseña debe tener mínimo 8 caracteres.'
            )

        return password
    
@login_required
@rol_requerido(['Administrador'])
def restablecer_password_usuario(request, id):

    usuario = Usuario.objects.get(id=id)

    if request.method == 'POST':

        form = CambiarPasswordForm(request.POST)

        if form.is_valid():

            nueva_password = form.cleaned_data['password']

            usuario.set_password(nueva_password)
            usuario.save()

            Auditoria.objects.create(
                usuario=request.user,
                accion='REINICIO DE CONTRASEÑA',
                descripcion=(
                    f'El administrador {request.user.username} '
                    f'restableció la contraseña del usuario '
                    f'{usuario.username}.'
                )
            )

            messages.success(
                request,
                'Contraseña restablecida correctamente.'
            )

            return redirect('usuarios')

        else:

            messages.error(
                request,
                'No se pudo restablecer la contraseña.'
            )

    else:

        form = CambiarPasswordForm()

    return render(
        request,
        'usuarios/restablecer_password.html',
        {
            'form': form,
            'usuario': usuario
        }
    )