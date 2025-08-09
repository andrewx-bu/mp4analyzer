# Video display canvas with drag functionality.
from typing import Optional
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QLabel, QFrame
from PyQt6.QtGui import QPixmap


class DraggableVideoLabel(QLabel):
    """A QLabel that can be dragged within its parent container."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drag_offset: Optional[QPoint] = None

    def set_image(self, pixmap: QPixmap):
        self.setPixmap(pixmap)
        self.adjustSize()

    def start_drag(self, mouse_pos: QPoint):
        self._drag_offset = mouse_pos - self.pos()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def update_drag(self, mouse_pos: QPoint):
        if self._drag_offset:
            self.move(mouse_pos - self._drag_offset)

    def end_drag(self):
        self._drag_offset = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    @property
    def is_dragging(self) -> bool:
        return self._drag_offset is not None


class VideoDisplayCanvas(QFrame):
    """A canvas widget that displays video frames with drag functionality."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #222222;")
        self.video_label = DraggableVideoLabel(self)

    def display_frame(self, pixmap: QPixmap):
        self.video_label.set_image(pixmap)

    def clear_display(self):
        self.video_label.clear()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.video_label.start_drag(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if self.video_label.is_dragging:
            self.video_label.update_drag(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.video_label.end_drag()
