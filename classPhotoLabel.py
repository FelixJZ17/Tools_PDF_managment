
from PyQt6.QtWidgets import (QLabel, QRubberBand)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint

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
    