# Timeline widget for displaying frame information as a bar graph.
from typing import Callable, List, Optional
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QScrollArea
from models import FrameData


class TimelineBarGraph(QWidget):
    """
    A widget that displays video frame information as a bar graph.
    
    Each bar represents a frame, with height proportional to frame size
    and color indicating frame type (I, P, B frames).
    """
    
    # Color scheme for different frame types
    FRAME_TYPE_COLORS = {
        '?': QColor('gray'),      # Unknown
        'I': QColor('red'),       # Intra (keyframe)
        'P': QColor('blue'),      # Predicted
        'B': QColor('green'),     # Bidirectional
        'S': QColor('gray'),      # Switching
        'SI': QColor('gray'),     # Switching Intra
        'SP': QColor('gray'),     # Switching Predicted
        'BI': QColor('gray'),     # Bidirectional Intra
    }
    
    # Layout constants
    BAR_WIDTH = 25           # Width of each bar in pixels
    BAR_SPACING = 1          # Space between bars
    LABEL_HEIGHT = 40        # Space reserved for frame labels
    BACKGROUND_COLOR = QColor(34, 34, 34)  # Dark background
    
    def __init__(self, frame_selection_callback: Callable[[int], None]):
        super().__init__()
        self._frame_data: List[FrameData] = []
        self._selected_frame_index: int = -1
        self._hovered_frame_index: int = -1
        self._frame_selection_callback = frame_selection_callback
        self._scroll_area: Optional[QScrollArea] = None
        
        self._setup_widget()
    
    def _setup_widget(self):
        """Initialize widget properties."""
        self.setMouseTracking(True)
        self.setMinimumHeight(self.LABEL_HEIGHT + 80)
    
    def set_scroll_area(self, scroll_area: QScrollArea):
        """Associate this widget with a scroll area for auto-scrolling."""
        self._scroll_area = scroll_area
    
    def set_frame_data(self, frame_data: List[FrameData]):
        """
        Set the frame data to display.
        
        Args:
            frame_data: List of FrameData objects to display
        """
        self._frame_data = frame_data
        self._selected_frame_index = 0 if frame_data else -1
        self._hovered_frame_index = -1
        
        # Calculate required width
        total_width = self._calculate_total_width()
        self.setMinimumWidth(total_width)
        self.resize(total_width, self.height())
        
        self.update()
        
        if self._scroll_area:
            self._center_view_on_selected_frame()
    
    def set_selected_frame(self, frame_index: int):
        """
        Set the selected frame index.
        
        Args:
            frame_index: Index of frame to select
        """
        if frame_index != self._selected_frame_index:
            self._selected_frame_index = frame_index
            self.update()
            
            if self._scroll_area:
                self._center_view_on_selected_frame()
    
    def _calculate_total_width(self) -> int:
        """Calculate total width needed for all bars."""
        if not self._frame_data:
            return 0
        
        num_frames = len(self._frame_data)
        total_bar_width = num_frames * self.BAR_WIDTH
        total_spacing = max(0, num_frames - 1) * self.BAR_SPACING
        
        return total_bar_width + total_spacing
    
    def _center_view_on_selected_frame(self):
        """Center the scroll view on the selected frame."""
        if not self._scroll_area or not self._frame_data or self.width() == 0:
            return
        
        # Calculate x position of selected frame center
        selected_frame_center_x = self._get_frame_center_x(self._selected_frame_index)
        
        # Calculate desired scroll position
        viewport_width = self._scroll_area.viewport().width()
        max_scroll_value = max(0, self.width() - viewport_width)
        
        desired_scroll_position = selected_frame_center_x - viewport_width // 2
        final_scroll_position = max(0, min(max_scroll_value, desired_scroll_position))
        
        self._scroll_area.horizontalScrollBar().setValue(final_scroll_position)
    
    def _get_frame_center_x(self, frame_index: int) -> int:
        """Get the x coordinate of the center of a frame bar."""
        frame_x = frame_index * (self.BAR_WIDTH + self.BAR_SPACING)
        return frame_x + self.BAR_WIDTH // 2
    
    def _get_frame_index_at_position(self, x_position: float) -> int:
        """
        Get the frame index at a given x position.
        
        Args:
            x_position: X coordinate
            
        Returns:
            Frame index, or -1 if no frames
        """
        if not self._frame_data:
            return -1
        
        cell_width = self.BAR_WIDTH + self.BAR_SPACING
        frame_index = int(x_position // cell_width)
        
        return max(0, min(len(self._frame_data) - 1, frame_index))
    
    def _get_max_frame_size(self) -> int:
        """Get the maximum frame size for scaling bars."""
        if not self._frame_data:
            return 1
        
        max_size = max(frame.size_bytes for frame in self._frame_data)
        return max_size if max_size > 0 else 1
    
    # Mouse event handlers
    def mouseMoveEvent(self, event):
        """Handle mouse move events for hover effects."""
        frame_index = self._get_frame_index_at_position(event.position().x())
        
        if frame_index != self._hovered_frame_index:
            self._hovered_frame_index = frame_index
            self.update()
        
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        if self._hovered_frame_index != -1:
            self._hovered_frame_index = -1
            self.update()
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for frame selection."""
        if event.button() == Qt.MouseButton.LeftButton and self._frame_data:
            frame_index = self._get_frame_index_at_position(event.position().x())
            self.set_selected_frame(frame_index)
            
            if self._frame_selection_callback:
                self._frame_selection_callback(frame_index)
            
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for frame navigation."""
        if not self._frame_data:
            return
        
        # Determine direction
        step = -1 if event.angleDelta().y() > 0 else 1
        new_frame_index = max(0, min(len(self._frame_data) - 1, self._selected_frame_index + step))
        
        if new_frame_index != self._selected_frame_index:
            self._selected_frame_index = new_frame_index
            self.update()
            
            if self._frame_selection_callback:
                self._frame_selection_callback(new_frame_index)
        
        if self._scroll_area:
            self._center_view_on_selected_frame()
        
        event.accept()
    
    def paintEvent(self, event):
        """Handle paint events to draw the timeline."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.BACKGROUND_COLOR)
        
        if not self._frame_data:
            return
        
        self._draw_frame_bars(painter)
        self._draw_frame_labels(painter)
        self._draw_hover_highlight(painter)
        self._draw_selection_indicator(painter)
        
        painter.end()
    
    def _draw_frame_bars(self, painter: QPainter):
        """Draw the frame size bars."""
        max_frame_size = self._get_max_frame_size()
        usable_height = self.height() - self.LABEL_HEIGHT
        
        for i, frame_data in enumerate(self._frame_data):
            # Calculate bar dimensions
            bar_height = int(frame_data.size_bytes / max_frame_size * (usable_height - 10))
            bar_x = i * (self.BAR_WIDTH + self.BAR_SPACING)
            bar_y = usable_height - bar_height
            
            # Get color for frame type
            color = self.FRAME_TYPE_COLORS.get(frame_data.frame_type, QColor('gray'))
            
            # Highlight if hovered
            if i == self._hovered_frame_index:
                color = color.lighter(150)
            
            # Draw the bar
            bar_rect = QRect(bar_x, bar_y, self.BAR_WIDTH, bar_height)
            painter.fillRect(bar_rect, color)
    
    def _draw_frame_labels(self, painter: QPainter):
        """Draw frame number labels."""
        usable_height = self.height() - self.LABEL_HEIGHT
        
        # Set font properties
        font = painter.font()
        font.setPointSizeF(font.pointSizeF() * 1.25)
        font.setBold(True)
        painter.setFont(font)
        
        for i in range(len(self._frame_data)):
            bar_x = i * (self.BAR_WIDTH + self.BAR_SPACING)
            
            # Draw rotated frame number
            painter.save()
            painter.translate(bar_x + self.BAR_WIDTH // 2 - 5, usable_height + 2)
            painter.rotate(90)
            painter.drawText(0, 0, f"#{i}")
            painter.restore()
    
    def _draw_hover_highlight(self, painter: QPainter):
        """Draw hover highlight effect."""
        if self._hovered_frame_index >= 0:
            bar_x = self._hovered_frame_index * (self.BAR_WIDTH + self.BAR_SPACING)
            highlight_rect = QRect(bar_x, 0, self.BAR_WIDTH, self.height())
            painter.fillRect(highlight_rect, QColor(255, 255, 255, 40))
    
    def _draw_selection_indicator(self, painter: QPainter):
        """Draw the selection indicator."""
        if 0 <= self._selected_frame_index < len(self._frame_data):
            usable_height = self.height() - self.LABEL_HEIGHT
            center_x = self._get_frame_center_x(self._selected_frame_index)
            
            # Draw selection marker at top
            marker_color = QColor('yellow')
            marker_width = 8
            marker_height = 14
            
            marker_rect = QRect(
                center_x - marker_width // 2,
                0,
                marker_width,
                marker_height
            )
            painter.fillRect(marker_rect, marker_color)
            
            # Draw selection line
            pen = QPen(marker_color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawLine(center_x, marker_height, center_x, usable_height)