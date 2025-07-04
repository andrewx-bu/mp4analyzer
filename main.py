import sys
import av
from typing import Optional, List
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QFrame, QScrollArea, QTextEdit, QSlider,
    QSplitter, QFileDialog, QPushButton, QSizePolicy
)
from loadmp4.load import MP4Loader, VideoInfo

class MP4Analyzer(QMainWindow):
    """
    Main application window for the MP4 Analyzer GUI.
    Handles UI setup, video loading, playback, and frame display.
    """
    def __init__(self):
        super().__init__()
        self.current_video: Optional[VideoInfo] = None
        self.container = None               # PyAV container
        self.video_stream = None            # PyAV video stream
        self.frame_images: List[QImage] = []
        self.current_frame_idx: int = 0

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
        # 1) Load metadata
        self.current_video = MP4Loader.load_video(file_path)
        if not self.current_video:
            self.log_box.append(f"❌ Failed to load metadata: {file_path}")
            return
        self._update_ui_with_video_info()

        # 2) Initialize PyAV container and decode frames
        try:
            self.container = av.open(file_path)
            self.video_stream = next(s for s in self.container.streams if s.type == 'video')
            self.frame_images.clear()
            # Decode and convert each frame to QImage
            for packet in self.container.demux(self.video_stream):
                for frame in packet.decode():
                    rgb = frame.to_ndarray(format='rgb24')
                    h, w, _ = rgb.shape
                    img = QImage(rgb.data, w, h, QImage.Format.Format_RGB888)
                    self.frame_images.append(img.copy())
        except Exception as e:
            self.log_box.append(f"❌ Error decoding frames: {e}")
            return

        # 3) Setup slider and controls
        total = len(self.frame_images)
        self.playback_slider.setMinimum(0)
        self.playback_slider.setMaximum(max(0, total - 1))
        self.playback_slider.setValue(0)
        self.playback_slider.valueChanged.connect(
            lambda value: self._display_frame(value)
        )

        # Connect navigation buttons
        self.prev_button.clicked.connect(lambda: self._step_frame(-1))
        self.next_button.clicked.connect(lambda: self._step_frame(1))

        # Display first frame
        self._display_frame(0)
        self.log_box.append(f"✅ Loaded: {file_path} ({total} frames)")

    def _update_ui_with_video_info(self):
        """
        Display loaded video's metadata in the metadata box.
        """
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
        """
        Render the frame at `index` and update UI elements.
        """
        if not self.frame_images:
            return
        # Clamp index
        idx = max(0, min(index, len(self.frame_images) - 1))
        img = self.frame_images[idx]
        pix = QPixmap.fromImage(img)
        
        # Scale the pixmap to fit the available space while maintaining aspect ratio
        scaled_pix = pix.scaled(
            self.scroll_area.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_frame.setPixmap(scaled_pix)
        
        # Update frame counter
        self.current_frame_idx = idx
        total = len(self.frame_images)
        self.frame_counter_label.setText(f"{idx+1} / {total}")

        # Reflect slider position without feedback loop
        if self.playback_slider.value() != idx:
            self.playback_slider.blockSignals(True)
            self.playback_slider.setValue(idx)
            self.playback_slider.blockSignals(False)

    def _step_frame(self, offset: int):
        """
        Move current frame index by exactly `offset` (-1 or +1) and display the new frame.
        Clamps to valid frame range.
        """
        if not self.frame_images:
            return
        
        new_idx = self.current_frame_idx + offset
        # Clamp to valid range
        new_idx = max(0, min(new_idx, len(self.frame_images) - 1))
        
        # Only update if we actually moved
        if new_idx != self.current_frame_idx:
            self._display_frame(new_idx)

    def _init_ui(self):
        """Setup main layout splitters and styling."""
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
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
        """Build left panel: metadata, filters, log, playback controls."""
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        self.metadata_box = self._create_text_box("MP4 Metadata")
        self.filters_box = self._create_text_box("Sequences/Filters")
        self.log_box = self._create_text_box("Log Messages")
        left_splitter.addWidget(self.metadata_box)
        left_splitter.addWidget(self.filters_box)
        left_splitter.addWidget(self.log_box)
        left_splitter.addWidget(self._create_playback_control())
        left_splitter.setSizes([400,160,160,80])
        return left_splitter

    def _create_right_panel(self) -> QSplitter:
        """Build right panel: frame display and timeline placeholder."""
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Create scroll area for the video frame
        self.scroll_area = QScrollArea()
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidgetResizable(True)  # This is important
        
        # Create the video frame label
        self.video_frame = QLabel("Frame Display Area")
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        self.video_frame.setScaledContents(True)  # Allow the pixmap to scale
        
        self.scroll_area.setWidget(self.video_frame)
        
        right_splitter.addWidget(self.scroll_area)
        self.timeline_bar = QLabel("Timeline Bar")
        self.timeline_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_splitter.addWidget(self.timeline_bar)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)
        return right_splitter

    def _create_text_box(self, placeholder: str) -> QTextEdit:
        """Helper: a read-only text box with placeholder text."""
        box = QTextEdit()
        box.setReadOnly(True)
        box.setPlaceholderText(placeholder)
        return box

    def _create_playback_control(self) -> QFrame:
        """Create playback control UI: slider, counter, and nav buttons."""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        title = QLabel("Playback Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight:bold;border:none;")
        layout.addWidget(title)

        self.playback_slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.playback_slider)

        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0,0,0,0)
        self.frame_counter_label = QLabel("0 / 0")
        self.frame_counter_label.setFixedSize(80,25)
        self.frame_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.frame_counter_label, alignment=Qt.AlignmentFlag.AlignLeft)

        # Use actual buttons for navigation
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        for btn in (self.prev_button, self.next_button):
            btn.setFixedSize(40,25)
            btn.setStyleSheet("border:1px solid #555;background:#333;")
        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(0,0,0,0)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        bottom_layout.addWidget(nav, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(bottom)
        return frame

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MP4Analyzer()
    window.show()
    sys.exit(app.exec())
