# UI component builders for MP4Analyzer.
from typing import Callable
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QTextEdit, QLabel, QVBoxLayout, QHBoxLayout,
    QSplitter, QWidget, QSlider, QPushButton, QSpinBox
)
from canvas import VideoCanvas

# Reusable text box
def create_text_box(title: str) -> QTextEdit:
    box = QTextEdit()
    box.setReadOnly(True)
    box.setPlaceholderText(title)
    return box

# Playback controls: slider + nav buttons + counter
def create_playback_control(
    slider_changed: Callable[[int], None]
) -> QWidget:
    frame = QFrame()
    vbox = QVBoxLayout(frame)
    title_lbl = QLabel("Playback Control")
    title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_lbl.setStyleSheet("font-weight:bold;border:none;")
    vbox.addWidget(title_lbl)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.valueChanged.connect(slider_changed)
    vbox.addWidget(slider)

    bottom = QWidget()
    hbox = QHBoxLayout(bottom)
    hbox.setContentsMargins(0, 0, 0, 0)

    counter = QLabel("0 / 0")
    counter.setFixedSize(80, 25)
    counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
    hbox.addWidget(counter)

    prev_btn = QPushButton("<")
    next_btn = QPushButton(">")
    for btn in (prev_btn, next_btn):
        btn.setFixedSize(40, 25)
        btn.setStyleSheet("border:1px solid #555; background:#333;")
    nav = QWidget()
    nav_layout = QHBoxLayout(nav)
    nav_layout.setContentsMargins(0, 0, 2, 0)
    nav_layout.addWidget(prev_btn)
    nav_layout.addWidget(next_btn)
    hbox.addWidget(nav, alignment=Qt.AlignmentFlag.AlignRight)

    vbox.addWidget(bottom)
    return frame, slider, prev_btn, next_btn, counter

# Left panel: metadata, filters, log, playback
def create_left_panel(playback_widget) -> QSplitter:
    left = QSplitter(Qt.Orientation.Vertical)
    left.addWidget(create_text_box("MP4 Metadata"))
    left.addWidget(create_text_box("Sequences/Filters"))
    left.addWidget(create_text_box("Log Messages"))
    left.addWidget(playback_widget)
    left.setSizes([400, 160, 160, 80])
    return left

# Right panel: video display, control bar, timeline
def create_right_panel(
    open_clicked: Callable,
    snapshot_clicked: Callable,
    reset_clicked: Callable,
    zoom_changed: Callable[[int], None]
):
    right = QSplitter(Qt.Orientation.Vertical)

    # Video display
    canvas = VideoCanvas()
    video_lbl = canvas.label
    video_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    right.addWidget(canvas)

    # Control bar
    ctrl = QWidget()
    bar = QHBoxLayout(ctrl)
    bar.setContentsMargins(5, 5, 5, 5)
    open_btn = QPushButton("Open")
    open_btn.clicked.connect(open_clicked)
    open_btn.setStyleSheet("padding: 3px")
    snapshot_btn = QPushButton("Snapshot")
    snapshot_btn.clicked.connect(snapshot_clicked)
    snapshot_btn.setStyleSheet("padding: 3px")
    bar.addWidget(open_btn)
    bar.addWidget(snapshot_btn)
    bar.addStretch()
    reset_btn = QPushButton("Reset")
    reset_btn.clicked.connect(reset_clicked)
    reset_btn.setStyleSheet("padding: 3px")
    zoom_spin = QSpinBox()
    zoom_spin.setRange(1, 500)
    zoom_spin.setValue(100)
    zoom_spin.setSuffix("%")
    zoom_spin.valueChanged.connect(zoom_changed)
    zoom_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
    zoom_spin.setStyleSheet("padding-bottom: 1px")
    res_label = QLabel("--X--")
    res_label.setFixedSize(80, 25)
    res_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    bar.addWidget(reset_btn)
    bar.addWidget(zoom_spin)
    bar.addWidget(res_label)
    for i in range(bar.count()):
        item = bar.itemAt(i)
        if item.widget():
            bar.setAlignment(item.widget(), Qt.AlignmentFlag.AlignVCenter)
    right.addWidget(ctrl)

    # Timeline placeholder
    timeline = QLabel("Timeline Bar")
    timeline.setAlignment(Qt.AlignmentFlag.AlignCenter)
    right.addWidget(timeline)
    right.setStretchFactor(0, 3)
    right.setStretchFactor(2, 1)

    return canvas, video_lbl, zoom_spin, res_label, right