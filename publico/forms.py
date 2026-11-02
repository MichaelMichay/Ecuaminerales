import io
import uuid

from django import forms
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import AjusteCategoria, Comunicado, ImagenInsumo,Documento

MAX_PDF_BYTES = 10 * 1024 * 1024        # peso máximo del PDF subido
MAX_PDF = 10 * 1024 * 1024         # peso máximo de un documento PDF
MAX_BYTES = 5 * 1024 * 1024        # peso máximo del archivo subido
MAX_PIXELES = 40_000_000           # protege contra imágenes "bomba"
MAX_LADO = 1000                    # se reduce a 1000 px como máximo
FORMATOS_OK = {'JPEG', 'PNG', 'WEBP'}


def procesar_imagen(archivo):
    """
    Valida la imagen subida y devuelve una versión limpia: reducida, sin datos
    EXIF (GPS, cámara) y con un nombre aleatorio. No se confía en la extensión.
    """
    if archivo.size > MAX_BYTES:
        raise forms.ValidationError(
            'La imagen pesa más de 5 MB. Reduce su tamaño e inténtalo de nuevo.')
    try:
        archivo.seek(0)
        img = Image.open(archivo)
        if img.format not in FORMATOS_OK:
            raise forms.ValidationError('Formato no permitido. Usa JPG, PNG o WEBP.')
        if img.width * img.height > MAX_PIXELES:
            raise forms.ValidationError('La imagen tiene demasiados píxeles.')
        img = ImageOps.exif_transpose(img)
        img.load()
    except forms.ValidationError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        raise forms.ValidationError('No se pudo leer la imagen. Prueba con otro archivo.')

    tiene_alfa = img.mode in ('RGBA', 'LA') or (
        img.mode == 'P' and 'transparency' in img.info)
    img = img.convert('RGBA' if tiene_alfa else 'RGB')
    img.thumbnail((MAX_LADO, MAX_LADO), Image.Resampling.LANCZOS)

    salida = io.BytesIO()
    if tiene_alfa:
        img.save(salida, 'PNG', optimize=True)
        ext = 'png'
    else:
        img.save(salida, 'JPEG', quality=85, optimize=True)
        ext = 'jpg'
    return ContentFile(salida.getvalue(), name=f'{uuid.uuid4().hex}.{ext}')


class ImagenModelForm(forms.ModelForm):
    """Base: campo de imagen opcional con opción de quitarla."""
    imagen = forms.ImageField(
        required=False, label='Imagen',
        help_text='JPG, PNG o WEBP, hasta 5 MB. Se reduce y optimiza sola. '
                  'Funciona mejor en horizontal (proporción 4:3).',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp'}))
    quitar_imagen = forms.BooleanField(
        required=False, label='Quitar la imagen actual',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        self._anterior = inst.imagen.name if inst.pk and inst.imagen else ''
        if not self._anterior:
            self.fields.pop('quitar_imagen')

    def clean_imagen(self):
        archivo = self.cleaned_data.get('imagen')
        if isinstance(archivo, UploadedFile):      # llegó un archivo nuevo
            return procesar_imagen(archivo)
        return archivo

    def clean(self):
        data = super().clean()
        if ('imagen' not in self.errors and data.get('quitar_imagen')
                and not isinstance(data.get('imagen'), ContentFile)):
            data['imagen'] = ''                      # '' = vaciar el campo
        return data

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if commit and self._anterior and obj.imagen.name != self._anterior:
            obj.imagen.storage.delete(self._anterior)   # borra la imagen reemplazada
        return obj


class ComunicadoForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = ['titulo', 'resumen', 'contenido', 'fecha_publicacion', 'documento', 'publicado']
        widgets = {
            'documento': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'fecha_publicacion': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'publicado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AjusteCategoriaForm(ImagenModelForm):
    color_auto = forms.BooleanField(
        required=False, label='Color automático',
        help_text='Déjalo marcado para que el sistema asigne el color.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    field_order = ['visible', 'imagen', 'quitar_imagen', 'descripcion_publica',
                   'orden', 'color_auto', 'color', 'mostrar_insumos', 'detalle_stock']

    class Meta:
        model = AjusteCategoria
        fields = ['visible', 'imagen', 'descripcion_publica', 'orden', 'color',
                  'mostrar_insumos', 'detalle_stock']
        widgets = {
            'visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'descripcion_publica': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'mostrar_insumos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'detalle_stock': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['color'].label = 'Color (si no es automático)'
        self.fields['color_auto'].initial = not (self.instance.color)

    def clean(self):
        data = super().clean()
        if data.get('color_auto'):
            data['color'] = ''
        return data


class ImagenInsumoForm(ImagenModelForm):
    class Meta:
        model = ImagenInsumo
        fields = ['imagen']

    def clean(self):
        data = super().clean()
        if 'imagen' not in self.errors and not data.get('imagen') and not self._anterior:
            self.add_error('imagen', 'Selecciona una imagen.')
        return data

class DocumentoForm(forms.ModelForm):
    archivo = forms.FileField(
        required=False, label='Archivo PDF',
        help_text='Solo PDF, hasta 10 MB.',
        widget=forms.FileInput(attrs={
            'class': 'form-control', 'accept': 'application/pdf,.pdf'}))

    class Meta:
        model = Documento
        fields = ['titulo', 'descripcion', 'archivo', 'fecha', 'orden', 'publicado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'publicado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        self._anterior = inst.archivo.name if inst.pk and inst.archivo else ''

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if isinstance(archivo, UploadedFile):          # llegó un archivo nuevo
            if not archivo.name.lower().endswith('.pdf'):
                raise forms.ValidationError('El archivo debe ser un PDF (.pdf).')
            if archivo.size > MAX_PDF:
                raise forms.ValidationError('El PDF pesa más de 10 MB.')
            archivo.seek(0)
            cabecera = archivo.read(1024)
            archivo.seek(0)
            if b'%PDF-' not in cabecera:               # no se confía en la extensión
                raise forms.ValidationError('El archivo no es un PDF válido.')
            archivo.name = f'{uuid.uuid4().hex}.pdf'   # nombre aleatorio en disco
        return archivo

    def clean(self):
        data = super().clean()
        if 'archivo' not in self.errors and not data.get('archivo') and not self._anterior:
            self.add_error('archivo', 'Selecciona un archivo PDF.')
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        nuevo = self.cleaned_data.get('archivo')
        if isinstance(nuevo, UploadedFile):
            obj.tamano = nuevo.size
        if commit:
            obj.save()
            if self._anterior and obj.archivo.name != self._anterior:
                obj.archivo.storage.delete(self._anterior)   # borra el PDF reemplazado
        return obj