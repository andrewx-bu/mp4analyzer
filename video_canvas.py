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
        self._drag_start_offset: Optional[QPoint] = None
        self._is_dragging = False
    
    def set_image(self, pixmap: QPixmap):
        """Set the image to display and adjust size."""
        self.setPixmap(pixmap)
        self.adjustSize()
    
    def start_drag(self, mouse_position: QPoint):
        """Initialize drag operation."""
        self._drag_start_offset = mouse_position - self.pos()
        self._is_dragging = True
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def update_drag_position(self, mouse_position: QPoint):
        """Update position during drag operation."""
        if self._is_dragging and self._drag_start_offset is not None:
            new_position = mouse_position - self._drag_start_offset
            self.move(new_position)
    
    def end_drag(self):
        """End drag operation."""
        self._is_dragging = False
        self._drag_start_offset = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    @property
    def is_dragging(self) -> bool:
        """Check if currently dragging."""
        return self._is_dragging


class VideoDisplayCanvas(QFrame):
    """
    A canvas widget that displays video frames with drag functionality.
    
    The canvas provides a dark background and contains a draggable label
    that displays the video frames.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_canvas()
        self._setup_video_label()
    
    def _setup_canvas(self):
        """Configure the canvas appearance."""
        self.setStyleSheet("background-color: #222222;")
    
    def _setup_video_label(self):
        """Create and configure the video display label."""
        self.video_label = DraggableVideoLabel(self)
    
    def display_frame(self, pixmap: QPixmap):
        """Display a video frame on the canvas."""
        self.video_label.set_image(pixmap)
    
    def clear_display(self):
        """Clear the current display."""
        self.video_label.clear()
    
    def reset_position(self):
        """Reset the video label to center of canvas."""
        if self.video_label.pixmap():
            label_size = self.video_label.size()
            canvas_size = self.size()
            
            # Center the label
            x = (canvas_size.width() - label_size.width()) // 2
            y = (canvas_size.height() - label_size.height()) // 2
            
            self.video_label.move(max(0, x), max(0, y))
    
    # Mouse event handlers for drag functionality
    def mousePressEvent(self, event):
        """Handle mouse press events for starting drag operations."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.video_label.start_drag(event.position().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drag operations."""
        if self.video_label.is_dragging:
            self.video_label.update_drag_position(event.position().toPoint())
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for ending drag operations."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.video_label.end_drag()
            event.accept()
        else:
            super().mouseReleaseEvent(event)