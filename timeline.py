from dataclasses import dataclass
from typing import Callable, List
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

@dataclass
class FrameInfo:
    size: int
    ftype: str

class TimelineBar(QWidget):
    """Widget showing frame sizes as a bar graph."""
    COLOR_MAP = {
        'I': QColor('red'),
        'P': QColor('blue'),
        'B': QColor('green'),
    }
    BAR_WIDTH = 25    # width of each bar in pixels
    PADDING = 1       # space between bars in pixels
    LABEL_SPACE = 35  # space at bottom for rotated labels

    def __init__(self, frame_selected: Callable[[int], None]):
        super().__init__()
        self._frames: List[FrameInfo] = []
        self._selected: int = -1
        self._hover: int = -1
        self._callback = frame_selected
        self.setMouseTracking(True)
        self.setMinimumHeight(self.LABEL_SPACE + 80)

    def set_frames(self, frames: List[FrameInfo]):
        self._frames = frames
        self._selected = 0 if frames else -1
        self._hover = -1
        # total width = number of bars * bar width + gaps between bars
        total_width = len(frames) * self.BAR_WIDTH + max(0, len(frames) - 1) * self.PADDING
        self.setMinimumWidth(total_width)
        self.resize(total_width, self.height())
        self.update()

    def set_selected(self, idx: int):
        if idx != self._selected:
            self._selected = idx
            self.update()

    def _index_at_pos(self, x: float) -> int:
        if not self._frames:
            return -1
        cell_w = self.BAR_WIDTH + self.PADDING
        idx = int(x // cell_w)
        return max(0, min(len(self._frames) - 1, idx))

    def mouseMoveEvent(self, event):
        idx = self._index_at_pos(event.position().x())
        if idx != self._hover:
            self._hover = idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover != -1:
            self._hover = -1
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._frames:
            idx = self._index_at_pos(event.position().x())
            self._selected = idx
            self.update()
            if self._callback:
                self._callback(idx)
            event.accept()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(34, 34, 34))
        if not self._frames:
            return
        bar_w = self.BAR_WIDTH
        pad = self.PADDING
        max_size = max(f.size for f in self._frames) or 1
        usable_h = self.height() - self.LABEL_SPACE
        for i, info in enumerate(self._frames):
            h = int(info.size / max_size * (usable_h - 10))
            x = int(i * (bar_w + pad))
            y = usable_h - h
            color = self.COLOR_MAP.get(info.ftype, QColor('gray'))
            if i == self._hover:
                color = color.lighter(150)
            painter.fillRect(QRect(x, y, bar_w, h), color)
            painter.save()
            font = painter.font()
            font.setPointSizeF(font.pointSizeF() * 1.25)
            font.setBold(True)
            painter.setFont(font)
            painter.translate(x + bar_w / 2 - 5, usable_h + 2)
            painter.rotate(90)
            painter.drawText(0, 0, f"#{i}")
            painter.restore()
        # Draw selected marker
        if 0 <= self._selected < len(self._frames):
            x_sel = int(self._selected * (bar_w + pad) + bar_w / 2)
            pen = QPen(QColor('yellow'))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(x_sel, 0, x_sel, usable_h)
        painter.end()
