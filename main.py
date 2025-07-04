# File: main.py
import sys
import av
from typing import Optional, List
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QFrame, QScrollArea, QTextEdit, QSlider,
    QSplitter, QFileDialog, QPushButton, QSizePolicy, QSpinBox
)
from loadmp4.load import MP4Loader, VideoInfo

class MP4Analyzer(QMainWindow):
    """
    Main application window for the MP4 Analyzer GUI.
    Handles UI setup, video loading, playback, zooming, and frame display.
    """
    def __init__(self):
        super().__init__()
        self.current_video: Optional[VideoInfo] = None
        self.container = None               # PyAV container
        self.video_stream = None            # PyAV video stream
        self.frame_images: List[QImage] = []
        self.current_frame_idx: int = 0
        self.zoom_factor: float = 1.0       # current zoom (1.0 = 100%)

        # Window setup
        self.setWindowTitle("MP4 Analyzer")
        self.setMinimumSize(1200, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Build UI and menu
        self._init_ui()
        self._init_menu()

    def _init_menu(self):
        """Create the File menu with an Open action."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        open_action = file_menu.addAction("Open MP4...")
        open_action.triggered.connect(self._open_file_dialog)

    def _open_file_dialog(self):
        """Prompt user to select an MP4 file, then load it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open MP4 File", "", "MP4 Files (*.mp4 *.mov);;All Files (*)"
        )
        if file_path:
            self._load_video(file_path)

    def _load_video(self, file_path: str):
        """
        Load metadata and frame data from the selected video file.
        """
        # Load metadata
        self.current_video = MP4Loader.load_video(file_path)
        if not self.current_video:
            self.log_box.append(f"❌ Failed to load metadata: {file_path}")
            return
        self._update_ui_with_video_info()

        # Decode frames
        try:
            self.container = av.open(file_path)
            self.video_stream = next(s for s in self.container.streams if s.type == 'video')
            self.frame_images.clear()
            for packet in self.container.demux(self.video_stream):
                for frame in packet.decode():
                    rgb = frame.to_ndarray(format='rgb24')
                    h, w, _ = rgb.shape
                    img = QImage(rgb.data, w, h, QImage.Format.Format_RGB888)
                    self.frame_images.append(img.copy())
        except Exception as e:
            self.log_box.append(f"❌ Error decoding frames: {e}")
            return

        # Setup playback slider
        total = len(self.frame_images)
        self.playback_slider.setMinimum(0)
        self.playback_slider.setMaximum(max(0, total - 1))
        self.playback_slider.setValue(0)
        self.playback_slider.valueChanged.connect(lambda v: self._display_frame(v))

        # Navigation buttons
        self.prev_button.clicked.connect(lambda: self._step_frame(-1))
        self.next_button.clicked.connect(lambda: self._step_frame(1))

        # Show first frame
        self._display_frame(0)
        self.log_box.append(f"✅ Loaded: {file_path} ({total} frames)")

    def _update_ui_with_video_info(self):
        """Display loaded video's metadata in the metadata box."""
        if not self.current_video:
            return
        info = (
            f"=== Video Metadata ===\n"
            f"Path: {self.current_video.path}\n"
            f"Resolution: {self.current_video.width}x{self.current_video.height}\n"
            f"Codec: {self.current_video.codec}\n"
            f"FPS: {self.current_video.fps:.2f}\n"
            f"Duration: {self.current_video.duration:.2f}s\n"
            f"Frames: {self.current_video.frame_count}\n"
        )
        self.metadata_box.setPlainText(info)

    def _display_frame(self, index: int):
        """Render the frame at `index`, apply zoom, and update UI."""
        if not self.frame_images:
            return
        idx = max(0, min(index, len(self.frame_images) - 1))
        img = self.frame_images[idx]
        pix = QPixmap.fromImage(img)

        # Update resolution label
        self.resolution_label.setText(f"{img.width()}x{img.height()}")

        # Apply zoom
        target_w = int(img.width() * self.zoom_factor)
        target_h = int(img.height() * self.zoom_factor)
        scaled = pix.scaled(
            target_w, target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_frame.setPixmap(scaled)

        # Frame counter
        self.current_frame_idx = idx
        self.frame_counter_label.setText(f"{idx+1} / {len(self.frame_images)}")

        # Sync slider
        if self.playback_slider.value() != idx:
            self.playback_slider.blockSignals(True)
            self.playback_slider.setValue(idx)
            self.playback_slider.blockSignals(False)

    def _step_frame(self, offset: int):
        """Advance frame by offset and refresh."""
        if not self.frame_images:
            return
        new_idx = max(0, min(self.current_frame_idx + offset, len(self.frame_images)-1))
        if new_idx != self.current_frame_idx:
            self._display_frame(new_idx)

    def _save_snapshot(self):
        """Save the current frame as a PNG file."""
        if not self.frame_images:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Snapshot", "", "PNG Files (*.png)")
        if path:
            pix = self.video_frame.pixmap()
            if pix:
                pix.save(path, "PNG")
                self.log_box.append(f"✅ Snapshot saved: {path}")

    def _reset_zoom(self):
        """Reset zoom to 100%."""
        self.zoom_spin.setValue(100)

    def _set_zoom(self, percent: int):
        """Adjust zoom factor and refresh frame."""
        self.zoom_factor = percent / 100.0
        self._display_frame(self.current_frame_idx)

    def _init_ui(self):
        """Setup main splitter and styles."""
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self._create_left_panel())
        main_splitter.addWidget(self._create_right_panel())
        main_splitter.setSizes([int(self.width()*0.2), int(self.width()*0.8)])

        layout = QHBoxLayout(self.central_widget)
        layout.addWidget(main_splitter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("""
            QFrame, QTextEdit, QLabel, QPushButton {
                border: 1px solid #555;
                background: #222;
                color: white;
            }
            QSplitter::handle { background: #444; width:2px; height:2px; }
        """)

    def _create_left_panel(self) -> QSplitter:
        """Left side: metadata, filters, log, playback controls."""
        left = QSplitter(Qt.Orientation.Vertical)
        self.metadata_box = self._create_text_box("MP4 Metadata")
        self.filters_box = self._create_text_box("Sequences/Filters")
        self.log_box = self._create_text_box("Log Messages")
        left.addWidget(self.metadata_box)
        left.addWidget(self.filters_box)
        left.addWidget(self.log_box)
        left.addWidget(self._create_playback_control())
        left.setSizes([400,160,160,80])
        return left

    def _create_right_panel(self) -> QSplitter:
        """Right side: frame view, control bar, timeline."""
        right = QSplitter(Qt.Orientation.Vertical)

        # Frame display in scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidgetResizable(True)
        self.video_frame = QLabel("Frame Display Area")
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_frame.setScaledContents(False)
        self.scroll_area.setWidget(self.video_frame)
        right.addWidget(self.scroll_area)

        # Control bar
        control = QWidget()
        bar = QHBoxLayout(control)
        bar.setContentsMargins(5, 5, 5, 5)

        # Left-aligned buttons (Open, Snapshot)
        open_btn = QPushButton("Open")
        open_btn.setStyleSheet("padding: 2px;")
        open_btn.clicked.connect(self._open_file_dialog)

        snapshot_btn = QPushButton("Snapshot")
        snapshot_btn.setStyleSheet("padding: 2px;")
        snapshot_btn.clicked.connect(self._save_snapshot)

        bar.addWidget(open_btn)
        bar.addWidget(snapshot_btn)

        # Add stretch to push remaining widgets to the right
        bar.addStretch()

        # Right-aligned widgets (Reset, Zoom SpinBox, Resolution Label)
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet("padding: 2px;")
        reset_btn.clicked.connect(self._reset_zoom)

        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(1, 500)
        self.zoom_spin.setValue(100)
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.valueChanged.connect(self._set_zoom)

        self.resolution_label = QLabel("--X--")
        self.resolution_label.setFixedSize(80, 25)
        self.resolution_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bar.addWidget(reset_btn)
        bar.addWidget(self.zoom_spin)
        bar.addWidget(self.resolution_label)

        right.addWidget(control)

        # Timeline placeholder
        self.timeline_bar = QLabel("Timeline Bar")
        self.timeline_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.timeline_bar)
        right.setStretchFactor(0, 3)
        right.setStretchFactor(2, 1)

        return right

    def _create_text_box(self, placeholder: str) -> QTextEdit:
        """Helper to make a read-only text box."""
        box = QTextEdit()
        box.setReadOnly(True)
        box.setPlaceholderText(placeholder)
        return box

    def _create_playback_control(self) -> QFrame:
        """Build slider, frame counter, and nav buttons."""
        frame = QFrame()
        vbox = QVBoxLayout(frame)
        title = QLabel("Playback Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight:bold;border:none;")
        vbox.addWidget(title)

        self.playback_slider = QSlider(Qt.Orientation.Horizontal)
        vbox.addWidget(self.playback_slider)

        bottom = QWidget()
        hbox = QHBoxLayout(bottom)
        hbox.setContentsMargins(0,0,0,0)

        self.frame_counter_label = QLabel("0 / 0")
        self.frame_counter_label.setFixedSize(80, 25)
        self.frame_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox.addWidget(self.frame_counter_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        for btn in (self.prev_button, self.next_button):
            btn.setFixedSize(40, 25)
            btn.setStyleSheet("border:1px solid #555; background:#333;")
        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(0,0,2,0)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        hbox.addWidget(nav, alignment=Qt.AlignmentFlag.AlignRight)

        vbox.addWidget(bottom)
        return frame

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MP4Analyzer()
    window.show()
    sys.exit(app.exec())
