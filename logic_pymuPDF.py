import fitz  # PyMuPDF
from PyQt6.QtGui import QImage, QPixmap
import os

def obtener_total_paginas(ruta_pdf):
    try:
        with fitz.open(ruta_pdf) as doc:
            return doc.page_count
    except Exception as e:
        print(f"Error al abrir PDF: {e}")
        return 0

def obtener_pixmap_pdf(ruta_pdf, num_pagina, zoom=100):
    try:
        # Abrimos el documento
        doc = fitz.open(ruta_pdf)
        pagina = doc.load_page(num_pagina)
        
        # El zoom en PyMuPDF se maneja con una matriz (Matrix)
        # 1.0 es el tamaño original. 2.0 sería el doble.
        factor = zoom / 100
        matriz = fitz.Matrix(factor, factor)
        
        # Renderizamos la página a una imagen (pixmap de fitz)
        pix = pagina.get_pixmap(matrix=matriz)
        
        # Convertimos los datos crudos a QImage de PyQt
        # fitz.csRGB indica que usamos colores RGB
        fmt = QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        
        return QPixmap.fromImage(qimg)
    except Exception as e:
        print(f"Error en renderizado PyMuPDF: {e}")
        return None
    
def rotar_pdf(ruta_pdf, grados):
    try:
        doc = fitz.open(ruta_pdf)
        for pagina in doc:
            # La rotación en PyMuPDF es relativa al estado actual
            nueva_rot = (pagina.rotation + grados) % 360
            pagina.set_rotation(nueva_rot)
        
        nombre, ext = os.path.splitext(ruta_pdf)
        ruta_salida = f"{nombre}_rotado{ext}"
        doc.save(ruta_salida)
        doc.close()
        return ruta_salida
    except Exception as e:
        print(f"Error rotando PDF: {e}")
        return None
    
def unir_varios_pdfs(rutas_lista, ruta_salida):
    try:
        nuevo_doc = fitz.open()
        for ruta in rutas_lista:
            if ruta.lower().endswith('.pdf'):
                with fitz.open(ruta) as doc_temp:
                    nuevo_doc.insert_pdf(doc_temp)
        
        nuevo_doc.save(ruta_salida)
        nuevo_doc.close()
        return True
    except Exception as e:
        print(f"Error al unir PDFs: {e}")
        return False
    
def separar_pdf_en_paginas(ruta_pdf):
    try:
        doc = fitz.open(ruta_pdf)
        nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0]
        directorio_padre = os.path.dirname(ruta_pdf)
        
        # 1. Crear la subcarpeta con el nombre del PDF
        ruta_subcarpeta = os.path.join(directorio_padre, f"Separado_{nombre_base}")
        if not os.path.exists(ruta_subcarpeta):
            os.makedirs(ruta_subcarpeta)
            
        # 2. Extraer cada página
        for i in range(len(doc)):
            nuevo_doc = fitz.open()
            # Insertar la página (i) del documento original
            nuevo_doc.insert_pdf(doc, from_page=i, to_page=i)
            
            # Nombre del archivo individual (ej: Factura_Pag_01.pdf)
            nombre_pag = f"{nombre_base}_Pag_{i+1:02d}.pdf"
            nuevo_doc.save(os.path.join(ruta_subcarpeta, nombre_pag))
            nuevo_doc.close()
            
        doc.close()
        return True, ruta_subcarpeta
    except Exception as e:
        return False, str(e)
    
def crear_pdf_desde_imagenes(lista_rutas_imagenes, ruta_salida):
    try:
        nuevo_doc = fitz.open()  # Creamos un PDF vacío
        
        for ruta_img in lista_rutas_imagenes:
            # Abrimos la imagen como un documento temporal de una página
            img_doc = fitz.open(ruta_img)
            # Convertimos la imagen a un flujo de datos PDF
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()
            
            # Cargamos esos bytes como un PDF temporal y lo insertamos al final
            temp_pdf = fitz.open("pdf", pdf_bytes)
            nuevo_doc.insert_pdf(temp_pdf)
            temp_pdf.close()
            
        nuevo_doc.save(ruta_salida)
        nuevo_doc.close()
        return True
    except Exception as e:
        print(f"Error creando PDF desde imágenes: {e}")
        return False

def comprimir_pdf(ruta_pdf):
    try:
        doc = fitz.open(ruta_pdf)
        
        # Generar nombre automático
        nombre, ext = os.path.splitext(ruta_pdf)
        ruta_salida = f"{nombre}_compressed{ext}"
        
        # Guardar con opciones de optimización:
        # garbage=4: elimina objetos no usados y compacta el archivo
        # deflate=True: comprime los flujos de datos
        # clean=True: intenta reparar y limpiar la estructura interna
        doc.save(
            ruta_salida, 
            garbage=4, 
            deflate=True, 
            clean=True
        )
        doc.close()
        
        # Calcular ahorro de espacio
        tamano_original = os.path.getsize(ruta_pdf)
        tamano_nuevo = os.path.getsize(ruta_salida)
        ahorro = (1 - (tamano_nuevo / tamano_original)) * 100
        
        return True, ruta_salida, ahorro
    except Exception as e:
        return False, str(e), 0
    
def extraer_rango_pdf(ruta_pdf, lista_paginas, sufijo):
    """
    lista_paginas: lista de enteros [0, 2, 4...] (base 0)
    """
    try:
        doc_original = fitz.open(ruta_pdf)
        nuevo_doc = fitz.open()
        
        for i, p_no in enumerate(lista_paginas):
            # Validar que la página existe en el original
            if 0 <= p_no < len(doc_original):
                es_el_ultimo = 1 if i == len(lista_paginas) - 1 else 0
                nuevo_doc.insert_pdf(
                    doc_original, 
                    from_page=p_no, 
                    to_page=p_no, 
                    final=es_el_ultimo
                )
        
        # Construcción del nombre con el sufijo dinámico
        nombre, ext = os.path.splitext(ruta_pdf)
        ruta_salida = f"{nombre}{sufijo}{ext}"
        
        nuevo_doc.save(ruta_salida)
        nuevo_doc.close()
        doc_original.close()
        
        return True, ruta_salida
    except Exception as e:
        return False, str(e)
    
def pdf_a_imagenes(ruta_pdf, formato=".png"):
    try:
        doc = fitz.open(ruta_pdf)
        nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0]
        directorio_padre = os.path.dirname(ruta_pdf)
        
        # 1. Crear subcarpeta
        ruta_subcarpeta = os.path.join(directorio_padre, f"Imagenes_{nombre_base}")
        if not os.path.exists(ruta_subcarpeta):
            os.makedirs(ruta_subcarpeta)
            
        # 2. Renderizar cada página
        for i in range(len(doc)):
            pagina = doc.load_page(i)
            # Definimos la resolución (2 es el multiplicador para ~150-200 dpi)
            pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            nombre_img = f"{nombre_base}_Pag_{i+1:02d}{formato}"
            ruta_final_img = os.path.join(ruta_subcarpeta, nombre_img)
            
            pix.save(ruta_final_img)
            
        doc.close()
        return True, ruta_subcarpeta
    except Exception as e:
        return False, str(e)
    
def editar_metadata_pdf(ruta, nuevos_datos):
    """
    nuevos_datos: diccionario tipo {'title': 'Nuevo Título', 'author': 'Yo'}
    """
    try:
        doc = fitz.open(ruta)
        # Obtenemos los metadatos actuales para no borrar lo que no editamos
        meta = doc.metadata
        # Actualizamos solo los campos permitidos
        meta.update(nuevos_datos)
        
        doc.set_metadata(meta)
        doc.saveIncr() # Guarda los cambios en el mismo archivo de forma eficiente
        doc.close()
        return True
    except Exception as e:
        print(f"Error editando PDF: {e}")
        return False
    
def normalizar_a_a4(ruta_pdf):
    try:
        doc_original = fitz.open(ruta_pdf)
        nuevo_doc = fitz.open()
        
        # Definimos el tamaño A4 estándar en puntos
        # Ancho: 210mm (~595pts), Alto: 297mm (~842pts)
        a4_rect = fitz.PaperRect("a4") 
        
        for pagina in doc_original:
            # Creamos una página A4 vacía en el nuevo documento
            nueva_pag = nuevo_doc.new_page(width=a4_rect.width, height=a4_rect.height)
            
            # Calculamos el escalado para que el contenido original encaje (fit)
            # manteniendo la proporción (proporcional=True)
            nueva_pag.show_pdf_page(nueva_pag.rect, doc_original, pagina.number)
            
        nombre, ext = os.path.splitext(ruta_pdf)
        ruta_salida = f"{nombre}_A4{ext}"
        
        nuevo_doc.save(ruta_salida)
        nuevo_doc.close()
        doc_original.close()
        
        return True, ruta_salida
    except Exception as e:
        return False, str(e)