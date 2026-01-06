import os
import fitz
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pillow_heif


def obtener_lista_archivos(directorio):
    extensiones_validas = ('.pdf', '.png', '.jpg', '.jpeg', '.webp')
    lista_datos = []
    
    try:
        for archivo in os.listdir(directorio):
            if archivo.lower().endswith(extensiones_validas):
                ruta_completa = os.path.join(directorio, archivo)
                stats = os.stat(ruta_completa)
                
                # Tamaño en MB o KB
                tamano = stats.st_size / 1024
                unidad = "KB"
                if tamano > 1024:
                    tamano /= 1024
                    unidad = "MB"
                
                fecha = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                
                lista_datos.append({
                    "nombre": archivo,
                    "tamano": f"{tamano:.2f} {unidad}",
                    "fecha": fecha,
                    "ruta": ruta_completa
                })
    except Exception as e:
        print(f"Error al leer directorio: {e}")
        
    return lista_datos

def renombrar_archivo(ruta_completa, nuevo_nombre_sin_ext):
    directorio = os.path.dirname(ruta_completa)
    extension = os.path.splitext(ruta_completa)[1]
    nueva_ruta = os.path.join(directorio, nuevo_nombre_sin_ext + extension)
    
    # Validaciones
    if not nuevo_nombre_sin_ext.strip():
        return False, "El nombre no puede estar vacío."
    
    char_invalidos = '<>:"/\\|?*'
    if any(char in nuevo_nombre_sin_ext for char in char_invalidos):
        return False, f"El nombre contiene caracteres inválidos ({char_invalidos})."
        
    if os.path.exists(nueva_ruta):
        return False, "Ya existe un archivo con ese nombre en esta carpeta."
        
    try:
        os.rename(ruta_completa, nueva_ruta)
        return True, nueva_ruta
    except Exception as e:
        return False, str(e)
    
def gestionar_sustitucion(ruta_original, ruta_nueva, eliminar_original):
    """
    Si eliminar_original es True, borra el viejo y renombra el nuevo.
    Si es False, mantiene ambos.
    """
    if eliminar_original:
        try:
            os.remove(ruta_original)
            os.rename(ruta_nueva, ruta_original)
            return ruta_original
        except Exception as e:
            print(f"Error al sustituir: {e}")
            return ruta_nueva
    return ruta_nueva

def rotar_imagen(ruta_img, grados):
    """Rota una imagen y la guarda con un sufijo."""
    try:
        with Image.open(ruta_img) as img:
            # Expand=True asegura que si la imagen no es cuadrada, no se corte
            img_rotada = img.rotate(-grados, expand=True) 
            
            nombre, ext = os.path.splitext(ruta_img)
            ruta_salida = f"{nombre}_rotado{ext}"
            img_rotada.save(ruta_salida)
            return ruta_salida
    except Exception as e:
        print(f"Error rotando imagen: {e}")
        return None
    
def convertir_a_webp(ruta_imagen, calidad=80):
    """
    Convierte una imagen (JPG, PNG, etc.) a formato WebP.
    calidad: 1-100 (80 es el equilibrio ideal).
    """
    try:
        nombre, ext = os.path.splitext(ruta_imagen)
        ruta_salida = f"{nombre}_converted.webp"
        
        with Image.open(ruta_imagen) as img:
            # WebP soporta transparencia (RGBA), por lo que no hace falta convertir a RGB
            # a menos que quieras forzar un fondo blanco para PNGs transparentes.
            img.save(ruta_salida, "WEBP", quality=calidad)
            
        return True, ruta_salida
    except Exception as e:
        return False, str(e)
    
def obtener_metadatos_completos(ruta):
    info = {
        "Nombre": os.path.basename(ruta),
        "Tamaño": f"{os.path.getsize(ruta) / 1024:.2f} KB",
        "Ubicación": ruta,
        "Fecha Modificación": datetime.fromtimestamp(os.path.getmtime(ruta)).strftime('%Y-%m-%d %H:%M:%S')
    }

    # --- METADATOS PARA PDF ---
    if ruta.lower().endswith('.pdf'):
        try:
            doc = fitz.open(ruta)
            meta = doc.metadata  # Diccionario con autor, título, creador, etc.
            info["Formato"] = "PDF"
            info["Páginas"] = len(doc)
            for clave, valor in meta.items():
                if valor: info[f"PDF_{clave.capitalize()}"] = valor
            doc.close()
        except Exception as e:
            info["Error PDF"] = str(e)

    # --- METADATOS PARA IMÁGENES (EXIF) ---
    elif ruta.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        try:
            with Image.open(ruta) as img:
                info["Formato"] = img.format
                info["Resolución"] = f"{img.width}x{img.height}"
                info["Modo Color"] = img.mode
                
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, valor in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        # Solo añadir datos legibles y útiles
                        if isinstance(valor, (str, int, float)):
                            info[f"EXIF_{tag}"] = valor
        except Exception as e:
            info["Error Imagen"] = str(e)
            
    return info

def obtener_metadatos_completos(ruta):
    # Metadatos Básicos (Sistema)
    stats = os.stat(ruta)
    info = {
        "SISTEMA": {
            "Archivo": os.path.basename(ruta),
            "Tamaño": f"{stats.st_size / 1024:.2f} KB",
            "Creado": datetime.fromtimestamp(stats.st_ctime).strftime('%d/%m/%Y %H:%M'),
            "Modificado": datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M'),
            "Extensión": os.path.splitext(ruta)[1].upper()
        },
        "CONTENIDO": {},
        "OCULTO": {}
    }

    # --- CASO PDF ---
    if ruta.lower().endswith('.pdf'):
        try:
            doc = fitz.open(ruta)
            info["CONTENIDO"]["Páginas"] = len(doc)
            info["CONTENIDO"]["Seguridad"] = "Protegido" if doc.is_encrypted else "Abierto"
            
            for clave, valor in doc.metadata.items():
                if valor:
                    info["OCULTO"][f"PDF_{clave.capitalize()}"] = valor
            doc.close()
        except Exception as e:
            info["OCULTO"]["Error"] = f"No se pudo leer el PDF: {e}"

    # --- CASO IMÁGENES ---
    elif ruta.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        try:
            with Image.open(ruta) as img:
                info["CONTENIDO"]["Dimensiones"] = f"{img.width} x {img.height} px"
                info["CONTENIDO"]["Formato"] = img.format
                
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, valor in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        # Ignorar datos binarios muy largos que rompen la vista
                        if isinstance(valor, (str, int, float)):
                            info["OCULTO"][f"{tag}"] = valor
                        # Mención especial al GPS si existe
                        elif tag == "GPSInfo":
                            info["OCULTO"]["GPS"] = "Contiene coordenadas geográficas"
        except Exception as e:
            info["OCULTO"]["Error"] = f"No se pudo leer la imagen: {e}"
            
    return info

def guardar_metadatos(ruta, nuevos_datos):
    """
    Recibe la ruta y un diccionario con los campos editados.
    """
    try:
        if ruta.lower().endswith('.pdf'):
            doc = fitz.open(ruta)
            meta = doc.metadata
            # Mapeo de nombres amigables a claves internas de PyMuPDF
            mapeo = {
                "Título": "title",
                "Autor": "author",
                "Asunto": "subject",
                "Palabras Clave": "keywords"
            }
            for nombre_ui, clave_interna in mapeo.items():
                if nombre_ui in nuevos_datos:
                    meta[clave_interna] = nuevos_datos[nombre_ui]
            
            doc.set_metadata(meta)
            doc.saveIncr()
            doc.close()
            return True

        elif ruta.lower().endswith(('.jpg', '.jpeg')):
            img = Image.open(ruta)
            exif = img.getexif()
            # 315 es el tag para Artist/Author
            if "Autor" in nuevos_datos:
                exif[315] = nuevos_datos["Autor"]
            img.save(ruta, exif=exif)
            return True
            
        return False
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False
    
def editar_metadata_imagen(ruta, autor=None):
    try:
        img = Image.open(ruta)
        exif = img.getexif()
        
        if autor:
            # El código 315 corresponde a 'Artist' en EXIF
            exif[315] = autor 
            
        # Guardamos la imagen con los nuevos metadatos
        img.save(ruta, exif=exif)
        return True
    except Exception as e:
        print(f"Error editando Imagen: {e}")
        return False

# Registramos el soporte de HEIC en Pillow
pillow_heif.register_heif_opener()

def convertir_heic_a_jpg(ruta_heic):
    try:
        nombre, _ = os.path.splitext(ruta_heic)
        ruta_salida = f"{nombre}_converted.jpg"
        
        with Image.open(ruta_heic) as img:
            # Los HEIC suelen estar en modo color que JPG acepta bien, 
            # pero forzamos RGB por seguridad (evita errores con transparencias)
            img_rgb = img.convert("RGB")
            img_rgb.save(ruta_salida, "JPEG", quality=90)
            
        return True, ruta_salida
    except Exception as e:
        return False, str(e)
    
def aplicar_recorte(ruta_original, rect_ui, tamano_label, ruta_dest):
    try:
        with Image.open(ruta_original) as img:
            ancho_real, alto_real = img.size
            ancho_ui, alto_ui = tamano_label.width(), tamano_label.height()

            # Escalar las coordenadas de la UI a la imagen real
            factor_x = ancho_real / ancho_ui
            factor_y = alto_real / alto_ui

            left = rect_ui.left() * factor_x
            top = rect_ui.top() * factor_y
            right = rect_ui.right() * factor_x
            bottom = rect_ui.bottom() * factor_y

            img_recortada = img.crop((left, top, right, bottom))
            img_recortada.save(ruta_dest, "JPEG", quality=95)
            return True
    except Exception as e:
        print(f"Error en crop: {e}")
        return False