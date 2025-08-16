# Video display canvas with drag functionality.
from typing import Optional
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QLabel, QFrame
from PyQt6.QtGui import QPixmap


class DraggableVideoLabel(QLabel):
    """A QLabel that can display an image and be dragged within its parent."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drag_offset: Optional[QPoint] = None  # offset between click pos and widget pos

    def set_image(self, pixmap: QPixmap):
        """Set and resize label to fit pixmap."""
        self.setPixmap(pixmap)
        self.adjustSize()

    def start_drag(self, mouse_pos: QPoint):
        """Begin dragging from given mouse position."""
        self._drag_offset = mouse_pos - self.pos()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def update_drag(self, mouse_pos: QPoint):
        """Update position of label during drag."""
        if self._drag_offset:
            self.move(mouse_pos - self._drag_offset)

    def end_drag(self):
        """End drag and reset cursor."""
        self._drag_offset = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    @property
    def is_dragging(self) -> bool:
        """Return True if currently dragging."""
        return self._drag_offset is not None


class VideoDisplayCanvas(QFrame):
    """Canvas that hosts DraggableVideoLabel for displaying video frames."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #222222;")
        self.video_label = DraggableVideoLabel(self)  # actual frame display

    def display_frame(self, pixmap: QPixmap):
        """Render a new video frame."""
        self.video_label.set_image(pixmap)

    def clear_display(self):
        """Clear the displayed frame."""
        self.video_label.clear()

    # --- Mouse events delegate dragging to label ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.video_label.start_drag(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if self.video_label.is_dragging:
            self.video_label.update_drag(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.video_label.end_drag()
