# Timeline widget for displaying frame information as a bar graph.
from typing import Callable, List, Optional
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QScrollArea, QToolTip
from models import FrameData


class TimelineBarGraph(QWidget):
    """A widget that displays video frame info (size, type, refs) as a bar graph."""

    # Color mapping for frame types
    FRAME_COLORS = {
        "I": QColor("red"),
        "P": QColor("blue"),
        "B": QColor("green"),
        "?": QColor("gray"),
        "S": QColor("gray"),
        "SI": QColor("gray"),
        "SP": QColor("gray"),
        "BI": QColor("gray"),
    }

    BAR_WIDTH = 13
    BAR_SPACING = 1
    LABEL_HEIGHT = 40
    MIN_BAR_HEIGHT = 1

    def __init__(self, frame_selection_callback: Callable[[int], None]):
        super().__init__()
        self._frame_data: List[FrameData] = []     # list of frames to visualize
        self._selected_frame = -1                  # current selection index
        self._hovered_frame = -1                   # frame under mouse cursor
        self._callback = frame_selection_callback  # notify main window when selected
        self._scroll_area: Optional[QScrollArea] = None

        self.setMouseTracking(True)
        self.setMinimumHeight(self.LABEL_HEIGHT + 80)

    def set_scroll_area(self, scroll_area: QScrollArea):
        """Attach scroll area for auto-centering selected frame."""
        self._scroll_area = scroll_area

    def set_frame_data(self, frame_data: List[FrameData]):
        """Load new frame data and reset selection/hover state."""
        self._frame_data = frame_data
        self._selected_frame = 0 if frame_data else -1
        self._hovered_frame = -1

        # Update widget width to fit bars
        total_width = (
            len(frame_data) * (self.BAR_WIDTH + self.BAR_SPACING) if frame_data else 0
        )
        self.setMinimumWidth(total_width)
        self.resize(total_width, self.height())
        self.update()

        # Auto-scroll to current selection
        if self._scroll_area:
            self._center_on_selected()

    def set_selected_frame(self, frame_index: int):
        """Select a frame and scroll into view."""
        if frame_index != self._selected_frame:
            self._selected_frame = frame_index
            self.update()
            if self._scroll_area:
                self._center_on_selected()

    def _center_on_selected(self):
        """Center scroll position on selected frame."""
        if not self._scroll_area or not self._frame_data:
            return

        center_x = (
            self._selected_frame * (self.BAR_WIDTH + self.BAR_SPACING)
            + self.BAR_WIDTH // 2
        )
        viewport_width = self._scroll_area.viewport().width()
        scroll_pos = max(
            0, min(center_x - viewport_width // 2, self.width() - viewport_width)
        )
        self._scroll_area.horizontalScrollBar().setValue(scroll_pos)

    def _get_frame_at_x(self, x: float) -> int:
        """Return frame index at given x coordinate."""
        if not self._frame_data:
            return -1
        frame_idx = int(x // (self.BAR_WIDTH + self.BAR_SPACING))
        return max(0, min(len(self._frame_data) - 1, frame_idx))

    def mouseMoveEvent(self, event):
        """Update hovered frame + show tooltip with frame info."""
        hovered = self._get_frame_at_x(event.position().x())
        if hovered != self._hovered_frame:
            self._hovered_frame = hovered
            self.update()

        if 0 <= hovered < len(self._frame_data):
            frame = self._frame_data[hovered]
            text = (
                f"Frame: {hovered}\n"
                f"Bytes: {frame.size_bytes}\n"
                f"PTS: {frame.pts}\n"
                f"Decode Order: {frame.decode_order}\n"
                f"Timestamp: {frame.timestamp:.3f}"
            )
            QToolTip.showText(event.globalPosition().toPoint(), text, self)

    def leaveEvent(self, event):
        """Clear hover highlight when mouse leaves widget."""
        if self._hovered_frame != -1:
            self._hovered_frame = -1
            self.update()
        QToolTip.hideText()

    def mousePressEvent(self, event):
        """On click: select frame + trigger callback."""
        if event.button() == Qt.MouseButton.LeftButton and self._frame_data:
            frame_idx = self._get_frame_at_x(event.position().x())
            self.set_selected_frame(frame_idx)
            if self._callback:
                self._callback(frame_idx)

    def wheelEvent(self, event):
        """Mouse wheel to step frames left/right."""
        if not self._frame_data:
            return

        step = -1 if event.angleDelta().y() > 0 else 1
        new_idx = max(0, min(len(self._frame_data) - 1, self._selected_frame + step))

        if new_idx != self._selected_frame:
            self._selected_frame = new_idx
            self.update()
            if self._callback:
                self._callback(new_idx)
            if self._scroll_area:
                self._center_on_selected()

    def paintEvent(self, event):
        """Draw frame bars, labels, highlights, and ref links."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(34, 34, 34))  # background

        if not self._frame_data:
            return

        # Scale bar heights relative to largest frame size
        max_size = max(f.size_bytes for f in self._frame_data) or 1
        usable_height = self.height() - self.LABEL_HEIGHT

        # --- Draw bars ---
        for i, frame in enumerate(self._frame_data):
            bar_height = int(frame.size_bytes / max_size * (usable_height - 10))
            if bar_height < self.MIN_BAR_HEIGHT:
                bar_height = self.MIN_BAR_HEIGHT
            bar_x = i * (self.BAR_WIDTH + self.BAR_SPACING)
            bar_y = usable_height - bar_height

            rect = QRect(bar_x, bar_y, self.BAR_WIDTH, bar_height)

            color = self.FRAME_COLORS.get(frame.frame_type, QColor("gray"))
            if i == self._hovered_frame:
                color = color.lighter(150)  # brighten on hover

            painter.fillRect(rect, color)

        # --- Frame index labels ---
        font = painter.font()
        font.setPointSizeF(font.pointSizeF() * 1.15)
        font.setBold(True)
        painter.setFont(font)

        for i in range(len(self._frame_data)):
            bar_x = i * (self.BAR_WIDTH + self.BAR_SPACING)
            painter.save()
            painter.translate(bar_x + self.BAR_WIDTH // 2 - 5, usable_height + 2)
            painter.rotate(90)
            painter.drawText(0, 0, f"#{i}")
            painter.restore()

        # --- Hover highlight (semi-transparent overlay) ---
        if self._hovered_frame >= 0:
            bar_x = self._hovered_frame * (self.BAR_WIDTH + self.BAR_SPACING)
            painter.fillRect(
                QRect(bar_x, 0, self.BAR_WIDTH, self.height()),
                QColor(255, 255, 255, 40),
            )

        # --- Selection indicator + reference links ---
        if 0 <= self._selected_frame < len(self._frame_data):
            center_x = (
                self._selected_frame * (self.BAR_WIDTH + self.BAR_SPACING)
                + self.BAR_WIDTH // 2
            )

            # Selection marker at top
            marker_h = 14
            painter.fillRect(QRect(center_x - 3, 0, 5, marker_h), QColor("yellow"))

            # Vertical highlight line
            usable_height = self.height() - self.LABEL_HEIGHT
            pen = QPen(QColor("yellow"), 3)
            painter.setPen(pen)
            y_top = marker_h - 6
            painter.drawLine(center_x, y_top, center_x, usable_height)

            # Draw references (prev/next IP)
            pen = QPen(QColor("yellow"), 2)
            painter.setPen(pen)
            frame = self._frame_data[self._selected_frame]
            for ref_idx in (frame.ref_prev, frame.ref_next):
                if ref_idx is None or ref_idx == self._selected_frame:
                    continue
                if not (0 <= ref_idx < len(self._frame_data)):
                    continue

                ref_center_x = (
                    ref_idx * (self.BAR_WIDTH + self.BAR_SPACING) + self.BAR_WIDTH // 2
                )
                # Horizontal link + vertical line at reference bar
                painter.drawLine(center_x, y_top, ref_center_x, y_top)
                painter.drawLine(ref_center_x, y_top, ref_center_x, usable_height)
