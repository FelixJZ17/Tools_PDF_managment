import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QScrollArea, QFrame, QTableWidget, QTableWidgetItem,
                             QLineEdit, QMessageBox, QAbstractItemView, QInputDialog,
                             QDialog, QTextEdit, QFormLayout, QRubberBand)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint
from PyQt6.QtGui import QImage, QPixmap
import os

# Importamos nuestros módulos personalizados
import logic_images
import logic_pymuPDF

# --- Configuración (IMPORTANTE) ---
# Si usas Windows, DEBES descomentar y ajustar esta línea con la ruta
# a la carpeta 'bin' de la instalación/binarios de Poppler.
# RUTA_POPPLER = r'C:\ruta\a\poppler-23.01.0\Library\bin' 
RUTA_POPPLER = None  # Déjalo así si Poppler está en el PATH del sistema (Linux/macOS)
# ---------------------------------

class DocManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Documentos Poppler")
        self.resize(1200, 800)
        self.archivos_actuales = []
        self.zoom_actual = 100
        self.ruta_archivo_actual = ""

        self.init_ui()
        self.seleccionar_directorio() # Pedir directorio al iniciar

    def init_ui(self):
        # Widget Principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout_principal = QVBoxLayout(main_widget)

        # --- SECCIÓN SUPERIOR: Directorio ---
        top_layout = QHBoxLayout()
        self.lbl_directorio = QLabel("Directorio no seleccionado")
        btn_cambiar_dir = QPushButton("Cambiar Directorio")
        btn_cambiar_dir.clicked.connect(self.seleccionar_directorio)
        top_layout.addWidget(self.lbl_directorio, stretch=1)
        top_layout.addWidget(btn_cambiar_dir)
        layout_principal.addLayout(top_layout)

        # --- SECCIÓN CONTROLES: Zoom y Navegación ---
        controles_layout = QHBoxLayout()
        controles_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 1. Grupo Archivos (Ant/Sig + Info)
        grupo_archivos = QVBoxLayout()
        self.btn_archivo_ant = QPushButton("<< Anterior Archivo")
        self.btn_archivo_sig = QPushButton("Siguiente Archivo >>")
        self.btn_archivo_ant.setFixedWidth(150)
        self.btn_archivo_sig.setFixedWidth(150)
        grupo_archivos.addWidget(self.btn_archivo_ant)
        grupo_archivos.addWidget(self.btn_archivo_sig)
        
        self.lbl_info_archivos = QLabel("0 / 0")
        self.lbl_info_archivos.setMargin(10)

        controles_layout.addLayout(grupo_archivos)
        controles_layout.addWidget(self.lbl_info_archivos)
        controles_layout.addSpacing(20) # Espacio entre grupos

        # 2. Grupo Zoom (+/- + Info)
        grupo_zoom = QVBoxLayout()
        self.btn_zoom_in = QPushButton("Zoom +")
        self.btn_zoom_out = QPushButton("Zoom -")
        self.btn_zoom_in.setFixedWidth(100)
        self.btn_zoom_out.setFixedWidth(100)
        grupo_zoom.addWidget(self.btn_zoom_in)
        grupo_zoom.addWidget(self.btn_zoom_out)
        
        self.lbl_info_zoom = QLabel("100%")
        self.lbl_info_zoom.setMargin(10)
        
        controles_layout.addLayout(grupo_zoom)
        controles_layout.addWidget(self.lbl_info_zoom)
        controles_layout.addSpacing(20)

        # 3. Grupo Páginas (Sig/Ant + Info)
        grupo_paginas = QVBoxLayout()
        self.btn_pag_ante = QPushButton("< Página")
        self.btn_pag_sig = QPushButton("Página >")
        self.btn_pag_sig.setFixedWidth(100)
        self.btn_pag_ante.setFixedWidth(100)
        grupo_paginas.addWidget(self.btn_pag_sig)
        grupo_paginas.addWidget(self.btn_pag_ante)
        
        self.lbl_info_paginas = QLabel("Pág: 0 / 0")
        self.lbl_info_paginas.setMargin(10)
        
        controles_layout.addLayout(grupo_paginas)
        controles_layout.addWidget(self.lbl_info_paginas)

        # Añadir todo al layout principal
        layout_principal.addLayout(controles_layout)

        # Dentro de init_ui, conecta los botones que creamos antes:
        self.btn_pag_sig.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_pag_ante.clicked.connect(lambda: self.cambiar_pagina(-1))
        self.btn_zoom_in.clicked.connect(lambda: self.cambiar_zoom(20))
        self.btn_zoom_out.clicked.connect(lambda: self.cambiar_zoom(-20))
        self.btn_archivo_sig.clicked.connect(self.ir_archivo_siguiente)
        self.btn_archivo_ant.clicked.connect(self.ir_archivo_anterior)
        
        # --- SECCIÓN RENOMBRAR ---
        renombrar_layout = QHBoxLayout()
        self.txt_nuevo_nombre = QLineEdit()
        self.txt_nuevo_nombre.setPlaceholderText("Nuevo nombre del archivo...")
        self.txt_nuevo_nombre.returnPressed.connect(self.ejecutar_renombrado)
        
        self.lbl_extension = QLabel(".ext")
        self.lbl_extension.setStyleSheet("font-weight: bold; color: gray;")
        
        btn_renombrar = QPushButton("Renombrar")
        btn_renombrar.setFixedWidth(100)
        btn_renombrar.clicked.connect(self.ejecutar_renombrado)
        
        renombrar_layout.addWidget(QLabel("Editar nombre:"))
        renombrar_layout.addWidget(self.txt_nuevo_nombre)
        renombrar_layout.addWidget(self.lbl_extension)
        renombrar_layout.addWidget(btn_renombrar)
        
        layout_principal.addLayout(renombrar_layout)

        # --- SECCIÓN CENTRAL: Tres columnas ---
        cuerpo_layout = QHBoxLayout()

        # 1. Izquierda: Lista de archivos (Tabla con Scroll)
        self.tabla_archivos = QTableWidget(0, 3)
        self.tabla_archivos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Seleccionar fila completa
        self.tabla_archivos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # No editar celdas al hacer clic
        #self.tabla_archivos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection) # Solo uno a la vez
        self.tabla_archivos.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tabla_archivos.setHorizontalHeaderLabels(["Nombre", "Tamaño", "Fecha"])
        self.tabla_archivos.setMinimumWidth(300)
        # CONEXIÓN CRUCIAL:
        self.tabla_archivos.itemSelectionChanged.connect(self.archivo_seleccionado)
        cuerpo_layout.addWidget(self.tabla_archivos, stretch=1)

        # 2. Centro: Preview (Área de scroll para la imagen/PDF)
        self.preview_area = QScrollArea()
        self.preview_label = QLabel("Previsualización aquí")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setWidget(self.preview_label)
        self.preview_area.setWidgetResizable(True)
        cuerpo_layout.addWidget(self.preview_area, stretch=2)

        # 3. Derecha: Comandos
        comandos_layout = QVBoxLayout()
        comandos_frame = QFrame()
        comandos_frame.setLayout(comandos_layout)
        
        # Diccionario que mapea Nombre del Botón -> Método de la clase
        acciones = {
            "Girar Derecha": lambda: self.aplicar_rotacion(90),
            "Girar Izquierda": lambda: self.aplicar_rotacion(-90),
            # "Ver Metadatos": self.mostrar_ventana_metadatos, --> comento porque la otra queda más completa
            "Ver Metadatos": self.mostrar_ventana_metadatos_completos,
            "Editar Metadatos": self.mostrar_ventana_metadatos_editar,
            "Ejecutar Modo Recorte": self.ejecutar_modo_recorte,
            # Aquí empiezan las herramientas de pdfs
            "Unir PDFs": self.unir_pdfs,
            "Crear PDF desde imágenes": self.crear_pdf_desde_imagenes,
            "Separar PDF": self.separar_pdf,
            "Comprimir PDF": self.ejecutar_comprimir_pdf,
            "Extraer Rango": self.ejecutar_extraer_rango,
            "Normalizar a A4": self.ejecutar_normalizar_a4,
            # Aquí empiezo con la herramientas de imágenes
            "Convertir a Imágenes": self.convertir_a_imagenes,
            "Pasar a .WebP": lambda: self.ejecutar_pasar_a_webp,
            "Convertir HEIC a JPG": self.ejecutar_heic_to_jpg

        }
        
        for nombre, funcion in acciones.items():
            btn = QPushButton(nombre)
            btn.setFixedWidth(180) # Opcional: para que todos midan lo mismo
            btn.clicked.connect(funcion) # Conectamos directamente a la función
            comandos_layout.addWidget(btn)
        
        comandos_layout.addStretch() # Empuja los botones hacia arriba
        cuerpo_layout.addWidget(comandos_frame, stretch=0)

        layout_principal.addLayout(cuerpo_layout)

    def seleccionar_directorio(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if dir_path:
            self.lbl_directorio.setText(dir_path)
            self.archivos_actuales = logic_images.obtener_lista_archivos(dir_path)
            self.actualizar_tabla()

    def actualizar_tabla(self):
        self.tabla_archivos.setRowCount(0)
        for archivo in self.archivos_actuales:
            row = self.tabla_archivos.rowCount()
            self.tabla_archivos.insertRow(row)
            self.tabla_archivos.setItem(row, 0, QTableWidgetItem(archivo["nombre"]))
            self.tabla_archivos.setItem(row, 1, QTableWidgetItem(archivo["tamano"]))
            self.tabla_archivos.setItem(row, 2, QTableWidgetItem(archivo["fecha"]))

    def archivo_seleccionado(self):
        fila = self.tabla_archivos.currentRow()
        if fila < 0:
            return

        # En lugar de confiar solo en 'fila', obtenemos el nombre que el usuario ve
        nombre_archivo_celda = self.tabla_archivos.item(fila, 0).text()
        
        # Buscamos el objeto correcto en nuestra lista comparando el nombre
        archivo = next((a for a in self.archivos_actuales if a["nombre"] == nombre_archivo_celda), None)
        
        if archivo:
            self.ruta_archivo_actual = archivo["ruta"]
            
            # 1. Cargar nombre en el Entry para renombrar
            nombre_sin_ext, ext = os.path.splitext(archivo["nombre"])
            self.txt_nuevo_nombre.setText(nombre_sin_ext)
            self.lbl_extension.setText(ext)
            
            # 2. Resetear y Mostrar Preview
            self.pagina_actual = 0
            if self.ruta_archivo_actual.lower().endswith('.pdf'):
                self.mostrar_pdf(self.ruta_archivo_actual)
            else:
                self.mostrar_imagen(self.ruta_archivo_actual)
            
            # 3. Actualizar los números de "1 / 10", etc.
            self.actualizar_indicadores()

    def mostrar_pdf(self, ruta):
        try:
            print(f"Renderizando página {self.pagina_actual + 1} de: {ruta}")
            pixmap = logic_pymuPDF.obtener_pixmap_pdf(
                ruta, 
                self.pagina_actual, 
                self.zoom_actual
            )
            if pixmap:
                self.actualizar_preview(pixmap)
            else:
                self.preview_label.setText("Poppler devolvió una imagen vacía.")
        except Exception as e:
            print(f"CRASH EVITADO: {e}")
            self.preview_label.setText(f"Error crítico: {str(e)}")

    def mostrar_imagen(self, ruta):
        pixmap = QPixmap(ruta)
        if not pixmap.isNull():
            # Si la imagen es más grande que el monitor, podemos escalarla un poco
            # o dejar que el QScrollArea haga su trabajo.
            # Aplicamos el zoom actual al pixmap antes de mostrarlo
            ancho = int(pixmap.width() * (self.zoom_actual / 100))
            alto = int(pixmap.height() * (self.zoom_actual / 100))

            pixmap_escalado = pixmap.scaled(
            ancho, alto, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
            )

            self.actualizar_preview(pixmap_escalado)
        else:
            self.preview_label.setText("Error al cargar la imagen.")

    def actualizar_preview(self, pixmap):
        # Ajustar la imagen al ancho del scroll area si es muy grande
        # o dejarla en su tamaño original para el zoom
        self.preview_label.setPixmap(pixmap)
        self.preview_label.resize(pixmap.size())

    def cambiar_pagina(self, delta):
        total = logic_pymuPDF.obtener_total_paginas(self.ruta_archivo_actual)
        nueva_pag = self.pagina_actual + delta
        
        if 0 <= nueva_pag < total:
            self.pagina_actual = nueva_pag
            self.mostrar_pdf(self.ruta_archivo_actual)

        self.actualizar_indicadores()

    def cambiar_zoom(self, delta):
        nuevo_zoom = self.zoom_actual + delta
        if 20 <= nuevo_zoom <= 400: # Limites lógicos de zoom
            self.zoom_actual = nuevo_zoom
            self.mostrar_pdf(self.ruta_archivo_actual)

        self.actualizar_indicadores()

    def ir_archivo_siguiente(self):
        fila_actual = self.tabla_archivos.currentRow()
        total_filas = self.tabla_archivos.rowCount()
        
        if fila_actual < total_filas - 1:
            # Seleccionamos la siguiente fila
            self.tabla_archivos.setCurrentCell(fila_actual + 1, 0)
            # Forzamos que la tabla haga scroll si el archivo no es visible
            self.tabla_archivos.scrollToItem(self.tabla_archivos.currentItem())
        else:
            print("Ya estás en el último archivo.")

    def ir_archivo_anterior(self):
        fila_actual = self.tabla_archivos.currentRow()
        
        if fila_actual > 0:
            # Seleccionamos la fila anterior
            self.tabla_archivos.setCurrentCell(fila_actual - 1, 0)
            self.tabla_archivos.scrollToItem(self.tabla_archivos.currentItem())
        else:
            print("Ya estás en el primer archivo.")

    def actualizar_indicadores(self):
        # 1. Info de archivos
        fila_actual = self.tabla_archivos.currentRow() + 1
        total_archivos = len(self.archivos_actuales)
        self.lbl_info_archivos.setText(f"{fila_actual} / {total_archivos}")

        # 2. Info de Zoom
        self.lbl_info_zoom.setText(f"{self.zoom_actual}%")

        # 3. Info de Páginas
        if self.ruta_archivo_actual.lower().endswith('.pdf'):
            total_pags = logic_pymuPDF.obtener_total_paginas(self.ruta_archivo_actual)
            self.lbl_info_paginas.setText(f"Pág: {self.pagina_actual + 1} / {total_pags}")
        else:
            self.lbl_info_paginas.setText("Pág: 1 / 1")

    def ejecutar_renombrado(self):
        if not self.ruta_archivo_actual:
            return

        nuevo_nombre = self.txt_nuevo_nombre.text()
        exito, resultado = logic_images.renombrar_archivo(self.ruta_archivo_actual, nuevo_nombre)
        
        if exito:
            # 1. Guardar la nueva ruta como la actual
            nueva_ruta = resultado
            
            # 2. Actualizar la lista de archivos en memoria (para no re-escanear todo)
            # o simplemente volver a cargar el directorio para ser precisos:
            dir_actual = os.path.dirname(nueva_ruta)
            nuevo_nombre_completo = os.path.basename(nueva_ruta)
            self.archivos_actuales = logic_images.obtener_lista_archivos(dir_actual)
            
            # Desactivamos señales para que no se dispare 'archivo_seleccionado' mil veces
            self.tabla_archivos.blockSignals(True)
            
            # 3. Refrescar la tabla
            self.archivos_actuales = logic_images.obtener_lista_archivos(dir_actual)
            self.actualizar_tabla()

            
            # 4. Seleccionar el archivo renombrado en la tabla para no perder el foco
            for i in range(self.tabla_archivos.rowCount()):
                if self.tabla_archivos.item(i, 0).text() == nuevo_nombre_completo:
                    self.tabla_archivos.setCurrentCell(i, 0)
                    break

            # Reactivamos señales y actualizamos la ruta actual
            self.tabla_archivos.blockSignals(False)
            self.ruta_archivo_actual = nueva_ruta
            self.actualizar_indicadores()
            QMessageBox.warning(self, "Exito al renombrar", f"Renombrado con éxito")
        else:
            QMessageBox.warning(self, "Error al renombrar", f"No se pudo renombrar: {resultado}")

    def aplicar_rotacion(self, grados):
        if not self.ruta_archivo_actual:
            return

        ruta_original = self.ruta_archivo_actual
        ruta_nueva = None

        # 1. Aplicar rotación según tipo de archivo
        if self.ruta_archivo_actual.lower().endswith('.pdf'):
            ruta_nueva = logic_pymuPDF.rotar_pdf(self.ruta_archivo_actual, grados)
        else:
            ruta_nueva = logic_images.rotar_imagen(self.ruta_archivo_actual, grados)

        if not ruta_nueva:
            return
        
        # 2. Preguntar al usuario (por la naturaleza de la accion, no quiero que pregunte, sino que en esta concretamente que directamente sustituya)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Rotación completada")
        msg.setText("¿Deseas reemplazar el archivo original?")
        msg.setInformativeText("Si eliges 'No', se guardará como una copia nueva.")
        btn_si = msg.addButton("Sí, reemplazar", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("No, mantener copia", QMessageBox.ButtonRole.NoRole)
        #msg.exec()

        # 3. Procesar respuesta
        eliminar = True # (msg.clickedButton() == btn_si)
        ruta_final = logic_images.gestionar_sustitucion(ruta_original, ruta_nueva, eliminar)

        # 4. Refrescar interfaz
        dir_actual = os.path.dirname(ruta_final)
        self.archivos_actuales = logic_images.obtener_lista_archivos(dir_actual)
        self.actualizar_tabla()
        
        # Seleccionar el archivo resultante
        for i in range(self.tabla_archivos.rowCount()):
            if self.archivos_actuales[i]["nombre"] == os.path.basename(ruta_final):
                self.tabla_archivos.setCurrentCell(i, 0)
                break

    def unir_pdfs(self):
        items_seleccionados = self.tabla_archivos.selectedItems()
        # Como hay varias columnas, filtramos para obtener solo una referencia por fila
        filas = list(set(item.row() for item in items_seleccionados))
        
        if len(filas) < 2:
            QMessageBox.warning(self, "Atención", "Selecciona al menos 2 archivos para unir.")
            return

        # Obtener rutas de los seleccionados
        rutas_a_unir = [self.archivos_actuales[f]["ruta"] for f in filas]
        
        # Preguntar nombre para el nuevo archivo
        nombre_nuevo, ok = QInputDialog.getText(self, "Unir PDFs", "Nombre del nuevo archivo:")
        
        if ok and nombre_nuevo:
            if not nombre_nuevo.lower().endswith(".pdf"):
                nombre_nuevo += ".pdf"
                
            directorio = os.path.dirname(rutas_a_unir[0])
            ruta_final = os.path.join(directorio, nombre_nuevo)
            
            if logic_pymuPDF.unir_varios_pdfs(rutas_a_unir, ruta_final):
                QMessageBox.information(self, "Éxito", "PDFs unidos correctamente.")
                # Refrescar la tabla
                self.archivos_actuales = logic_images.obtener_lista_archivos(directorio)
                self.actualizar_indicadores()
                self.actualizar_tabla() 
            else:
                QMessageBox.critical(self, "Error", "No se pudieron unir los archivos.")
        
    def crear_pdf_desde_imagenes(self):
        items_seleccionados = self.tabla_archivos.selectedItems()
        filas = sorted(list(set(item.row() for item in items_seleccionados)))
        
        if not filas:
            QMessageBox.warning(self, "Atención", "Selecciona las imágenes que quieras incluir.")
            return

        # 1. Filtrar solo los archivos que sean imágenes
        formatos_imagen = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        rutas_imagenes = [
            self.archivos_actuales[f]["ruta"] 
            for f in filas 
            if self.archivos_actuales[f]["ruta"].lower().endswith(formatos_imagen)
        ]
        
        if not rutas_imagenes:
            QMessageBox.warning(self, "Atención", "Ninguno de los archivos seleccionados es una imagen válida.")
            return

        # 2. Pedir nombre para el nuevo PDF
        nombre_nuevo, ok = QInputDialog.getText(self, "Crear PDF", "Nombre del nuevo archivo PDF:")
        
        if ok and nombre_nuevo.strip():
            if not nombre_nuevo.lower().endswith(".pdf"):
                nombre_nuevo += ".pdf"
                
            directorio = os.path.dirname(rutas_imagenes[0])
            ruta_final = os.path.join(directorio, nombre_nuevo)
            
            # 3. Ejecutar la lógica
            if logic_pymuPDF.crear_pdf_desde_imagenes(rutas_imagenes, ruta_final):
                QMessageBox.information(self, "Éxito", f"PDF creado con {len(rutas_imagenes)} imágenes.")
                
                # Refrescar la tabla
                self.archivos_actuales = logic_images.obtener_lista_archivos(directorio)
                self.actualizar_tabla()
            else:
                QMessageBox.critical(self, "Error", "No se pudo crear el PDF.")
    
    def separar_pdf(self):
        if not self.ruta_archivo_actual or not self.ruta_archivo_actual.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Atención", "Selecciona un archivo PDF válido.")
            return

        # Confirmación
        respuesta = QMessageBox.question(
            self, "Separar PDF", 
            "¿Quieres separar este PDF en páginas individuales dentro de una subcarpeta?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            exito, resultado = logic_pymuPDF.separar_pdf_en_paginas(self.ruta_archivo_actual)
            
            if exito:
                QMessageBox.information(
                    self, "Éxito", 
                    f"Proceso completado.\nLos archivos están en: {resultado}"
                )
                # Refrescar la lista de archivos (por si la subcarpeta debe aparecer)
                dir_actual = os.path.dirname(self.ruta_archivo_actual)
                self.archivos_actuales = logic_images.obtener_lista_archivos(dir_actual)
                self.actualizar_tabla()
            else:
                QMessageBox.critical(self, "Error", f"No se pudo separar el PDF: {resultado}")
    
    def ejecutar_comprimir_pdf(self):
        if not self.ruta_archivo_actual or not self.ruta_archivo_actual.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Atención", "Selecciona un archivo PDF para comprimir.")
            return

        exito, resultado, ahorro = logic_pymuPDF.comprimir_pdf(self.ruta_archivo_actual)
        
        if exito:
            QMessageBox.information(
                self, "Compresión Finalizada", 
                f"Archivo guardado como:\n{os.path.basename(resultado)}\n\n"
                f"Ahorro estimado: {ahorro:.1f}%"
            )
            
            # Refrescar la lista para que aparezca el nuevo archivo
            dir_actual = os.path.dirname(self.ruta_archivo_actual)
            self.archivos_actuales = logic_images.obtener_lista_archivos(dir_actual)
            self.actualizar_tabla()
            
            # Seleccionar el nuevo archivo comprimido
            for i in range(self.tabla_archivos.rowCount()):
                if self.tabla_archivos.item(i, 0).text() == os.path.basename(resultado):
                    self.tabla_archivos.setCurrentCell(i, 0)
                    break
        else:
            QMessageBox.critical(self, "Error", f"No se pudo comprimir: {resultado}")

    def ejecutar_extraer_rango(self):
        if not self.ruta_archivo_actual or not self.ruta_archivo_actual.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Atención", "Selecciona un PDF para extraer páginas.")
            return

        # 1. Pedir el rango al usuario
        texto_rango, ok = QInputDialog.getText(
            self, "Extraer Páginas", 
            "Introduce el rango (ej: 1-3 o 1, 3, 5):"
        )

        if ok and texto_rango.strip():
            try:
                # Limpiar espacios y preparar el sufijo
                texto_limpio = texto_rango.replace(" ", "")
                paginas_a_extraer = []
                sufijo = ""

                # Caso Rango (2-8)
                if "-" in texto_limpio:
                    inicio, fin = map(int, texto_limpio.split("-"))
                    paginas_a_extraer = list(range(min(inicio, fin) - 1, max(inicio, fin)))
                    sufijo = f"_from{min(inicio, fin)}to{max(inicio, fin)}"
                
                # Caso Páginas sueltas (1, 3, 5) o Única (3)
                else:
                    partes = texto_limpio.split(",")
                    paginas_a_extraer = [int(p) - 1 for p in partes]
                    if len(partes) == 1:
                        sufijo = f"_page{partes[0]}"
                    else:
                        # Para varias sueltas, ponemos las primeras dos (ej: _pages1_3_etc)
                        sufijo = f"_pages{'_'.join(partes[:2])}"

                # 2. Llamar a la lógica enviando el sufijo personalizado
                exito, resultado = logic_pymuPDF.extraer_rango_pdf(
                    self.ruta_archivo_actual, 
                    paginas_a_extraer, 
                    sufijo
                )

                if exito:
                    QMessageBox.information(self, "Éxito", f"Creado: {os.path.basename(resultado)}")
                    self.archivos_actuales = logic_images.obtener_lista_archivos(os.path.dirname(resultado))
                    self.actualizar_tabla()
                
            except Exception as e:
                QMessageBox.warning(self, "Error", "Formato inválido. Usa '3' o '2-8'.")

    def convertir_a_imagenes(self):
        if not self.ruta_archivo_actual or not self.ruta_archivo_actual.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Atención", "Selecciona un archivo PDF válido.")
            return

        # Preguntamos si prefiere PNG o JPG
        items = [".png", ".jpg"]
        formato, ok = QInputDialog.getItem(self, "Formato de imagen", "Elige el formato de salida:", items, 0, False)

        if ok and formato:
            exito, resultado = logic_pymuPDF.pdf_a_imagenes(self.ruta_archivo_actual, formato)
            
            if exito:
                QMessageBox.information(
                    self, "Proceso completado", 
                    f"Se han extraído todas las páginas en:\n{resultado}"
                )
                # Refrescar para mostrar la subcarpeta
                self.archivos_actuales = logic_images.obtener_lista_archivos(os.path.dirname(self.ruta_archivo_actual))
                self.actualizar_tabla()
            else:
                QMessageBox.critical(self, "Error", f"Error al convertir: {resultado}")
    
    def ejecutar_pasar_a_webp(self):
        # 1. Obtener archivos seleccionados (soporta selección múltiple)
        items_seleccionados = self.tabla_archivos.selectedItems()
        filas = sorted(list(set(item.row() for item in items_seleccionados)))
        
        if not filas:
            QMessageBox.warning(self, "Atención", "Selecciona al menos una imagen (JPG o PNG).")
            return

        formatos_soportados = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
        exitos = 0
        errores = 0

        # 2. Iterar sobre la selección
        for fila in filas:
            ruta_original = self.archivos_actuales[fila]["ruta"]
            
            if ruta_original.lower().endswith(formatos_soportados):
                exito, resultado = logic_images.convertir_a_webp(ruta_original)
                if exito:
                    exitos += 1
                else:
                    errores += 1

        # 3. Feedback y refresco
        if exitos > 0:
            QMessageBox.information(self, "Proceso finalizado", 
                                    f"Se han convertido {exitos} imágenes a .WebP correctamente.")
            # Refrescamos la lista para ver los nuevos archivos
            dir_actual = os.path.dirname(self.archivos_actuales[filas[0]]["ruta"])
            self.archivos_actuales = logic_images.obtener_lista_archivos(dir_actual)
            self.actualizar_tabla()
        
        if errores > 0:
            QMessageBox.warning(self, "Aviso", f"No se pudieron convertir {errores} archivos.")

    def mostrar_ventana_metadatos(self):
        if not self.ruta_archivo_actual:
            QMessageBox.warning(self, "Atención", "Selecciona un archivo primero.")
            return

        # Obtener la info
        datos = logic_images.obtener_metadatos_completos(self.ruta_archivo_actual)
        
        # Crear una ventana de diálogo simple
        ventana = QDialog(self)
        ventana.setWindowTitle(f"Metadatos: {datos['Nombre']}")
        ventana.setMinimumSize(400, 500)
        
        layout = QVBoxLayout()
        
        # Usamos un área de texto para que el usuario pueda copiar la info si quiere
        visor = QTextEdit()
        visor.setReadOnly(True)
        
        # Formatear el texto para el visor
        texto_final = ""
        for k, v in datos.items():
            texto_final += f"<b>{k}:</b> {v}<br>"
        
        visor.setHtml(texto_final)
        
        layout.addWidget(visor)
        ventana.setLayout(layout)
        ventana.exec() # Abrir como ventana modal

    def mostrar_ventana_metadatos_completos(self):
        if not self.ruta_archivo_actual:
            QMessageBox.warning(self, "Atención", "Selecciona un archivo primero.")
            return

        datos = logic_images.obtener_metadatos_completos(self.ruta_archivo_actual)
        
        ventana = QDialog(self)
        ventana.setWindowTitle("Inspección de Metadatos")
        ventana.setMinimumSize(500, 600)
        
        layout = QVBoxLayout()
        
        visor = QTextEdit()
        visor.setReadOnly(True)
        
        # Construcción del HTML con colores para diferenciar secciones
        html = "<style>h3 { color: #2E86C1; border-bottom: 1px solid #AED6F1; } b { color: #283747; }</style>"
        
        for seccion, valores in datos.items():
            if valores: # Solo mostrar si la sección tiene datos
                html += f"<h3>{seccion}</h3>"
                for k, v in valores.items():
                    html += f"<b>{k}:</b> {v}<br>"
        
        visor.setHtml(html)
        
        layout.addWidget(QLabel(f"Análisis detallado de: <b>{datos['SISTEMA']['Archivo']}</b>"))
        layout.addWidget(visor)
        ventana.setLayout(layout)
        ventana.exec()

    def mostrar_ventana_metadatos_editar(self):
        if not self.ruta_archivo_actual:
            QMessageBox.warning(self, "Atención", "Selecciona un archivo.")
            return

        datos = logic_images.obtener_metadatos_completos(self.ruta_archivo_actual)
        self.inputs_editables = {} # Diccionario para guardar las cajas de texto

        ventana = QDialog(self)
        ventana.setWindowTitle(f"Editar Metadatos: {os.path.basename(self.ruta_archivo_actual)}")
        ventana.setMinimumSize(450, 500)
        
        main_layout = QVBoxLayout(ventana)
        
        # Área de scroll por si hay muchos metadatos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenedor = QWidget()
        form_layout = QFormLayout(contenedor)

        # Solo hacemos editables ciertos campos lógicos para evitar romper el archivo
        campos_editables = ["Título", "Autor", "Asunto", "Palabras Clave", "PDF_Title", "PDF_Author"]

        for seccion, valores in datos.items():
            if valores:
                label_seccion = QLabel(f"<b>--- {seccion} ---</b>")
                label_seccion.setStyleSheet("margin-top: 10px; color: #2E86C1;")
                form_layout.addRow(label_seccion)
                
                for k, v in valores.items():
                    # Si es un campo del sistema, lo dejamos solo lectura
                    if seccion == "SISTEMA" or "Dimensiones" in k:
                        label_fijo = QLabel(str(v))
                        label_fijo.setStyleSheet("color: gray;")
                        form_layout.addRow(f"{k}:", label_fijo)
                    else:
                        # Campo editable
                        input_txt = QLineEdit(str(v))
                        form_layout.addRow(f"{k}:", input_txt)
                        self.inputs_editables[k] = input_txt

        scroll.setWidget(contenedor)
        main_layout.addWidget(scroll)

        # Botón de Guardar
        btn_guardar = QPushButton("Guardar Cambios en Archivo")
        btn_guardar.setStyleSheet("background-color: #28B463; color: white; padding: 10px; font-weight: bold;")
        btn_guardar.clicked.connect(lambda: self.confirmar_guardar_metadatos(ventana))
        main_layout.addWidget(btn_guardar)

        ventana.exec()

    def confirmar_guardar_metadatos(self, ventana):
        # Recopilar datos de los inputs
        nuevos_valores = {k: v.text() for k, v in self.inputs_editables.items()}
        
        if logic_images.guardar_metadatos(self.ruta_archivo_actual, nuevos_valores):
            QMessageBox.information(self, "Éxito", "Metadatos actualizados correctamente.")
            ventana.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar los cambios.")

    def ejecutar_heic_to_jpg(self):
        items_seleccionados = self.tabla_archivos.selectedItems()
        filas = sorted(list(set(item.row() for item in items_seleccionados)))
        
        if not filas:
            QMessageBox.warning(self, "Atención", "Selecciona archivos .heic para convertir.")
            return

        exitos = 0
        for fila in filas:
            ruta = self.archivos_actuales[fila]["ruta"]
            if ruta.lower().endswith('.heic'):
                exito, resultado = logic_images.convertir_heic_a_jpg(ruta)
                if exito: exitos += 1

        if exitos > 0:
            QMessageBox.information(self, "Éxito", f"Se han convertido {exitos} archivos a JPG.")
            # Refrescar tabla
            self.archivos_actuales = logic_images.obtener_lista_archivos(os.path.dirname(ruta))
            self.actualizar_tabla()
        else:
            QMessageBox.warning(self, "Aviso", "No se encontraron archivos .heic en la selección.")

    def ejecutar_normalizar_a4(self):
        if not self.ruta_archivo_actual or not self.ruta_archivo_actual.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Atención", "Selecciona un archivo PDF.")
            return

        exito, resultado = logic_pymuPDF.normalizar_a_a4(self.ruta_archivo_actual)
        
        if exito:
            QMessageBox.information(self, "Éxito", f"PDF normalizado a A4:\n{os.path.basename(resultado)}")
            # Refrescar tabla
            self.archivos_actuales = logic_images.obtener_lista_archivos(os.path.dirname(resultado))
            self.actualizar_tabla()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo normalizar: {resultado}")

    def ejecutar_modo_recorte(self):
        if not self.ruta_archivo_actual:
            QMessageBox.warning(self, "Atención", "Selecciona una imagen primero.")
            return
            
        extensiones_imagen = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
        if not self.ruta_archivo_actual.lower().endswith(extensiones_imagen):
            QMessageBox.warning(self, "Atención", "El recorte visual solo está disponible para imágenes.")
            return

        # Lanzamos la ventana
        ventana_crop = CropWindow(self.ruta_archivo_actual, self)
        if ventana_crop.exec(): # Si el usuario guardó con éxito
            # Refrescamos la tabla y la preview
            self.archivos_actuales = logic_images.obtener_lista_archivos(os.path.dirname(self.ruta_archivo_actual))
            self.actualizar_tabla()
            QMessageBox.information(self, "Listo", "Imagen procesada correctamente.")

class PhotoLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        # Aquí es donde el usuario termina de seleccionar
        pass 

    def get_selection_rect(self):
        # Devuelve el área seleccionada relativa a la imagen mostrada
        return self.rubberBand.geometry()
    
class CropWindow(QDialog):
    def __init__(self, ruta_imagen, parent=None):
        super().__init__(parent)
        self.ruta_original = ruta_imagen
        self.setWindowTitle("Modo Recorte - Selecciona el área con el ratón")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # El visor interactivo
        self.canvas = PhotoLabel()
        self.pixmap_original = QPixmap(ruta_imagen)
        
        # Escalamos para que quepa en pantalla (ej: max 800px)
        pixmap_redimensionado = self.pixmap_original.scaled(
            800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.canvas.setPixmap(pixmap_redimensionado)
        self.canvas.setFixedSize(pixmap_redimensionado.size())
        
        layout.addWidget(self.canvas)
        
        # Botones de acción
        btns_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Confirmar Recorte")
        self.btn_cancelar = QPushButton("Cancelar")
        
        btns_layout.addWidget(self.btn_cancelar)
        btns_layout.addWidget(self.btn_guardar)
        layout.addLayout(btns_layout)
        
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.procesar_y_preguntar)

    def procesar_y_preguntar(self):
        rect = self.canvas.get_selection_rect()
        if rect.width() < 5 or rect.height() < 5:
            return # Selección demasiado pequeña
            
        # Diálogo de decisión de archivo
        msg = QMessageBox(self)
        msg.setWindowTitle("Guardar recorte")
        msg.setText("¿Cómo quieres guardar el recorte?")
        
        b_sustituir = msg.addButton("Sustituir Original", QMessageBox.ButtonRole.ActionRole)
        b_nuevo = msg.addButton("Crear '_crop'", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        ruta_base, ext = os.path.splitext(self.ruta_original)
        if msg.clickedButton() == b_sustituir:
            self.ruta_destino = self.ruta_original
        elif msg.clickedButton() == b_nuevo:
            self.ruta_destino = f"{ruta_base}_crop{ext}"
        else:
            return

        # Llamar a la lógica de logic_images (el código que escala coordenadas)
        exito = logic_images.aplicar_recorte(
            self.ruta_original, 
            rect, 
            self.canvas.size(), 
            self.ruta_destino
        )
        
        if exito:
            self.accept() # Cierra la ventana devolviendo éxitoclass CropWindow(QDialog):
    
    def __init__(self, ruta_imagen, parent=None):
        super().__init__(parent)
        self.ruta_original = ruta_imagen
        self.setWindowTitle("Modo Recorte - Selecciona el área con el ratón")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # El visor interactivo
        self.canvas = PhotoLabel()
        self.pixmap_original = QPixmap(ruta_imagen)
        
        # Escalamos para que quepa en pantalla (ej: max 800px)
        pixmap_redimensionado = self.pixmap_original.scaled(
            800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.canvas.setPixmap(pixmap_redimensionado)
        self.canvas.setFixedSize(pixmap_redimensionado.size())
        
        layout.addWidget(self.canvas)
        
        # Botones de acción
        btns_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Confirmar Recorte")
        self.btn_cancelar = QPushButton("Cancelar")
        
        btns_layout.addWidget(self.btn_cancelar)
        btns_layout.addWidget(self.btn_guardar)
        layout.addLayout(btns_layout)
        
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.procesar_y_preguntar)

    def procesar_y_preguntar(self):
        rect = self.canvas.get_selection_rect()
        if rect.width() < 5 or rect.height() < 5:
            return # Selección demasiado pequeña
            
        # Diálogo de decisión de archivo
        msg = QMessageBox(self)
        msg.setWindowTitle("Guardar recorte")
        msg.setText("¿Cómo quieres guardar el recorte?")
        
        b_sustituir = msg.addButton("Sustituir Original", QMessageBox.ButtonRole.ActionRole)
        b_nuevo = msg.addButton("Crear '_crop'", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        ruta_base, ext = os.path.splitext(self.ruta_original)
        if msg.clickedButton() == b_sustituir:
            self.ruta_destino = self.ruta_original
        elif msg.clickedButton() == b_nuevo:
            self.ruta_destino = f"{ruta_base}_crop{ext}"
        else:
            return

        # Llamar a la lógica de logic_images (el código que escala coordenadas)
        exito = logic_images.aplicar_recorte(
            self.ruta_original, 
            rect, 
            self.canvas.size(), 
            self.ruta_destino
        )
        
        if exito:
            self.accept() # Cierra la ventana devolviendo éxito


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = DocManager()
    ventana.show()
    sys.exit(app.exec())