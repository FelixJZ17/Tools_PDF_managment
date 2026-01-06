from PyQt6.QtWidgets import (QVBoxLayout, 
                             QHBoxLayout, QPushButton, QMessageBox, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import os

from classPhotoLabel import PhotoLabel
import logic_images


class CropWindow(QDialog):
    def __init__(self, ruta_imagen, parent=None):
        super().__init__(parent)
        self.ruta_original = ruta_imagen
        self.ruta_referencia_pdf = None

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
        if rect.width() < 10: return

        es_origen_pdf = hasattr(self, 'ruta_referencia_pdf')
        ruta_origen_real = self.ruta_referencia_pdf if es_origen_pdf else self.ruta_original

        # os.path.splitext sobre una ruta completa nos devuelve la ruta completa sin extensión
        ruta_base_completa, ext_original = os.path.splitext(ruta_origen_real)

        msg = QMessageBox(self)
        msg.setWindowTitle("Guardar Recorte")
        
        # Si es PDF, solo permitimos crear archivo nuevo (imagen)
        if es_origen_pdf:
            msg.setText("El recorte se guardará como una imagen nueva.")
            btn_nuevo = msg.addButton("Guardar como Imagen", QMessageBox.ButtonRole.ActionRole)
        else:
            msg.setText("¿Cómo quieres guardar el recorte?")
            btn_sustituir = msg.addButton("Sustituir Original", QMessageBox.ButtonRole.ActionRole)
            btn_nuevo = msg.addButton("Crear Nuevo archivo", QMessageBox.ButtonRole.ActionRole)
        
        msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() == btn_nuevo:
            # El recorte de un PDF siempre será .jpg o .png
            self.ruta_destino = f"{ruta_base_completa}_page{self.parent().pagina_actual + 1}_crop.jpg"
        elif not es_origen_pdf and msg.clickedButton() == btn_sustituir:
            self.ruta_destino = self.ruta_original
        else:
            return

        # Ejecutar recorte final
        logic_images.aplicar_recorte(self.ruta_original, rect, self.canvas.size(), self.ruta_destino)
        self.accept()
    
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
        
        b_nuevo = msg.addButton("Crear 'nuevo'", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        ruta_base, ext = os.path.splitext(self.ruta_original)
        if msg.clickedButton() == b_nuevo:
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
        else:
            QMessageBox.critical(self, "Error", "No se pudo crear el archivo final.")

