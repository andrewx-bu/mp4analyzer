# UI component builders for MP4 Analyzer application.
from typing import Callable, Tuple, List
import html
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QTextEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QWidget,
    QSlider,
    QPushButton,
    QSpinBox,
    QSizePolicy,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
)
from src.mp4analyzer import MP4Box
from ui.video_canvas import VideoDisplayCanvas
from ui.timeline_widget import TimelineBarGraph


class PlaybackControlWidget(QFrame):
    """Widget containing playback controls."""

    def __init__(self, on_frame_changed: Callable[[int], None]):
        super().__init__()
        self.on_frame_changed = on_frame_changed

        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.previous_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.frame_counter_label = QLabel("0 / 0")

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Playback Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; border: none;")
        layout.addWidget(title)

        # Slider
        layout.addWidget(self.frame_slider)

        # Bottom controls
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.frame_counter_label.setFixedSize(80, 25)
        self.frame_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.frame_counter_label)

        # Navigation buttons
        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 2, 0)

        for btn in [self.previous_button, self.next_button]:
            btn.setFixedSize(40, 25)
            btn.setStyleSheet("border: 1px solid #555; background: #333;")

        nav_layout.addWidget(self.previous_button)
        nav_layout.addWidget(self.next_button)
        bottom_layout.addWidget(nav, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(bottom)

        self.frame_slider.valueChanged.connect(self.on_frame_changed)

    def set_frame_range(self, max_frames: int):
        self.frame_slider.setRange(0, max(0, max_frames - 1))
        self.frame_slider.setValue(0)

    def set_current_frame(self, frame_index: int, total_frames: int):
        self.frame_counter_label.setText(f"{frame_index + 1} / {total_frames}")
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(frame_index)
        self.frame_slider.blockSignals(False)


class LeftPanelWidget(QSplitter):
    """Left panel containing metadata, filters, log, and playback controls."""

    def __init__(self, playback_control_widget: PlaybackControlWidget):
        super().__init__(Qt.Orientation.Vertical)

        self.metadata_view = QTextEdit()
        self.metadata_view.setPlaceholderText("MP4 Metadata")
        self.metadata_view.setReadOnly(True)

        metadata_container = QWidget()
        metadata_layout = QVBoxLayout(metadata_container)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.addWidget(self.metadata_view)

        self.boxes_tree = QTreeWidget()
        self.boxes_tree.setHeaderLabels(["Box", "Details"])
        self.boxes_tree.setTextElideMode(Qt.TextElideMode.ElideRight)

        monospace_font = QFont("Courier New")
        monospace_font.setStyleHint(QFont.StyleHint.Monospace)
        self.metadata_view.setFont(monospace_font)
        self.boxes_tree.setFont(monospace_font)

        self.boxes_tree.setStyleSheet(
            """
            QTreeView::item {
                border-right: 1px solid #555;
            }
            QTreeView::item:last {
                border-right: none;
            }
            QTreeView::item:selected {
                background: purple;
                color: white;
            }
            """
        )

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Log Messages")

        self.addWidget(metadata_container)
        self.addWidget(self.boxes_tree)
        self.addWidget(self.log_box)
        self.addWidget(playback_control_widget)

        self.setSizes([160, 440, 120, 80])

    def update_metadata(self, metadata_text: str):
        """Display formatted metadata text."""
        lines = metadata_text.splitlines()
        html_lines: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped == "Video track(s) info":
                html_lines.append("<b>Video track(s) info:</b>")
            elif stripped == "Audio track(s) info":
                html_lines.append("<b>Audio track(s) info:</b>")
            else:
                html_lines.append(html.escape(line))
        html_content = "<pre style='margin:0'>{}</pre>".format("\n".join(html_lines))
        self.metadata_view.setHtml(html_content)

    def update_boxes(self, boxes: List[MP4Box]):
        """Populate the boxes tree from parsed MP4 boxes."""
        self.boxes_tree.clear()

        light_blue_brush = QBrush(QColor("#ADD8E6"))

        def _add_box(parent: QTreeWidgetItem, box: MP4Box):
            props = box.properties()
            item = QTreeWidgetItem(parent)
            item.setText(1, "")

            box_name = props.get("box_name", "")
            label_text = f"<span style='color:red'>{box.type}</span>"
            if box_name:
                label_text += f" <span style='color:gray'>({box_name})</span>"
            label = QLabel(label_text)
            label.setStyleSheet("background: transparent;")
            label.setFont(self.boxes_tree.font())
            self.boxes_tree.setItemWidget(item, 0, label)

            for key, value in props.items():
                prop_item = QTreeWidgetItem(item, [key, str(value)])
                prop_item.setForeground(0, light_blue_brush)
                prop_item.setForeground(1, light_blue_brush)

            # Recurse into child boxes
            for child in box.children:
                _add_box(item, child)

        root = self.boxes_tree.invisibleRootItem()
        for box in boxes:
            _add_box(root, box)
        self.boxes_tree.expandToDepth(1)

    def add_log_message(self, message: str):
        self.log_box.append(message)


class VideoControlBar(QWidget):
    """Control bar with file operations and display settings."""

    def __init__(
        self,
        on_open_file: Callable,
        on_save_snapshot: Callable,
        on_reset_zoom: Callable,
        on_zoom_changed: Callable[[int], None],
    ):
        super().__init__()

        self.open_button = QPushButton("Open")
        self.snapshot_button = QPushButton("Snapshot")
        self.reset_button = QPushButton("Reset")
        self.zoom_spinbox = QSpinBox()
        self.resolution_label = QLabel("--x--")

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Buttons
        for btn in [self.open_button, self.snapshot_button, self.reset_button]:
            btn.setStyleSheet("padding: 3px")

        layout.addWidget(self.open_button)
        layout.addWidget(self.snapshot_button)
        layout.addStretch()
        layout.addWidget(self.reset_button)

        # Zoom control
        self.zoom_spinbox.setRange(1, 500)
        self.zoom_spinbox.setValue(100)
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_spinbox.setStyleSheet("padding-bottom: 1px")
        layout.addWidget(self.zoom_spinbox)

        # Resolution display
        self.resolution_label.setFixedSize(80, 25)
        self.resolution_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.resolution_label)

        # Connect signals
        self.open_button.clicked.connect(on_open_file)
        self.snapshot_button.clicked.connect(on_save_snapshot)
        self.reset_button.clicked.connect(on_reset_zoom)
        self.zoom_spinbox.valueChanged.connect(on_zoom_changed)

    def set_resolution_text(self, resolution: str):
        self.resolution_label.setText(resolution)

    def reset_zoom_value(self):
        self.zoom_spinbox.setValue(100)

    @property
    def current_zoom_percent(self) -> int:
        return self.zoom_spinbox.value()


class RightPanelWidget(QSplitter):
    """Right panel containing video display, controls, and timeline."""

    def __init__(
        self,
        on_open_file: Callable,
        on_save_snapshot: Callable,
        on_reset_zoom: Callable,
        on_zoom_changed: Callable[[int], None],
        on_frame_selected: Callable[[int], None],
    ):
        super().__init__(Qt.Orientation.Vertical)

        self.video_canvas = VideoDisplayCanvas()
        self.control_bar = VideoControlBar(
            on_open_file, on_save_snapshot, on_reset_zoom, on_zoom_changed
        )
        self.timeline_widget = TimelineBarGraph(on_frame_selected)

        # Timeline scroll area
        self.timeline_scroll_area = QScrollArea()
        self.timeline_scroll_area.setWidget(self.timeline_widget)
        self.timeline_scroll_area.setWidgetResizable(False)
        self.timeline_scroll_area.setMinimumHeight(150)
        self.timeline_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.timeline_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.timeline_scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.timeline_widget.set_scroll_area(self.timeline_scroll_area)

        self.addWidget(self.video_canvas)
        self.addWidget(self.control_bar)
        self.addWidget(self.timeline_scroll_area)

        self.setStretchFactor(0, 3)
        self.setStretchFactor(2, 1)


def create_main_layout(
    on_open_file: Callable,
    on_save_snapshot: Callable,
    on_reset_zoom: Callable,
    on_zoom_changed: Callable[[int], None],
    on_frame_changed: Callable[[int], None],
    on_frame_selected: Callable[[int], None],
) -> Tuple[QSplitter, PlaybackControlWidget, LeftPanelWidget, RightPanelWidget]:
    """Create the main application layout."""
    main_splitter = QSplitter(Qt.Orientation.Horizontal)

    playback_control = PlaybackControlWidget(on_frame_changed)
    left_panel = LeftPanelWidget(playback_control)
    right_panel = RightPanelWidget(
        on_open_file,
        on_save_snapshot,
        on_reset_zoom,
        on_zoom_changed,
        on_frame_selected,
    )

    main_splitter.addWidget(left_panel)
    main_splitter.addWidget(right_panel)
    main_splitter.setSizes([240, 960])

    return main_splitter, playback_control, left_panel, right_panel
