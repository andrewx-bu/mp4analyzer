from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QLabel, QFrame
from PyQt6.QtGui import QPixmap

class VideoCanvas(QFrame):
    # A fixed-size canvas that holds a draggable QLabel.
    def __init__(self, width: int = 960, height: int = 540):
        super().__init__()
        self.setFixedSize(width, height)
        self.setStyleSheet("background: black;")
        self.label = QLabel(self)
        self.label.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_offset: QPoint | None = None

    def set_pixmap(self, pix: QPixmap):
        self.label.setPixmap(pix)
        self.label.adjustSize()

    # mouse events for dragging the label
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.position().toPoint() - self.label.pos()
            self.label.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None:
            new_pos = event.position().toPoint() - self._drag_offset
            self.label.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = None
            self.label.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
