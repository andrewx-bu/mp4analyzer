import sys
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QScrollArea, QTextEdit, QSlider, QSplitter, QFileDialog, QSpacerItem,
    QSizePolicy
)
from loadmp4.load import MP4Loader, VideoInfo

class MP4Analyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_video: Optional[VideoInfo] = None
        self.setWindowTitle("MP4 Analyzer")
        self.setMinimumSize(1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.init_ui()
        self.init_menu()

    def init_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        open_action = file_menu.addAction("Open MP4...")
        open_action.triggered.connect(self.open_file_dialog)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open MP4 File",
            "",
            "MP4 Files (*.mp4 *.mov);;All Files (*)"
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path: str):
        self.current_video = MP4Loader.load_video(file_path)
        if self.current_video:
            self.update_ui_with_video_info()
        else:
            self.log_box.append(f"❌ Failed to load: {file_path}")

    def update_ui_with_video_info(self):
        if not self.current_video:
            return

        info = f"""=== Video Metadata ===
            Path: {self.current_video.path}
            Resolution: {self.current_video.width}x{self.current_video.height}
            Codec: {self.current_video.codec}
            FPS: {self.current_video.fps:.2f}
            Duration: {self.current_video.duration:.2f}s
            Frames: {self.current_video.frame_count}
        """
        self.metadata_box.setPlainText(info)
        self.log_box.append(f"✅ Loaded: {self.current_video.path}")

    def init_ui(self):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ==== LEFT COL ====
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Box 1: MP4 Metadata
        self.metadata_box = QTextEdit()
        self.metadata_box.setPlaceholderText("MP4 Metadata")
        left_splitter.addWidget(self.metadata_box)
        
        # Box 2: Sequences/Filters
        self.filters_box = QTextEdit()
        self.filters_box.setPlaceholderText("Sequences/Filters")
        left_splitter.addWidget(self.filters_box)
        
        # Box 3: Log Messages
        self.log_box = QTextEdit()
        self.log_box.setPlaceholderText("Log Messages")
        left_splitter.addWidget(self.log_box)
        
        # Box 4: Playback Control
        playback_control = QFrame()
        playback_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Playback Control")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; border: none;")

        # Top: Slider
        self.playback_slider = QSlider(Qt.Orientation.Horizontal)
        playback_layout.addWidget(title_label)
        playback_layout.addWidget(self.playback_slider)

        # Bottom: Frame counter and step buttons
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Left container for frame counter
        left_container = QWidget()
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.frame_counter_label = QLabel("0 / 0")
        self.frame_counter_label.setFixedSize(80, 25)
        self.frame_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.frame_counter_label)
        left_container.setLayout(left_layout)

        # Right container for < and > buttons
        right_container = QWidget()
        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 2, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.prev_button = QLabel("<")
        self.next_button = QLabel(">")
        for btn in [self.prev_button, self.next_button]:
            btn.setFixedSize(40, 25)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setStyleSheet("border: 1px solid #555; background: #333;")

        right_layout.addWidget(self.prev_button)
        right_layout.addWidget(self.next_button)
        right_container.setLayout(right_layout)

        bottom_layout.addWidget(left_container)
        bottom_layout.addWidget(right_container)

        bottom_row.setLayout(bottom_layout)
        playback_layout.addWidget(bottom_row)

        playback_control.setLayout(playback_layout)
        left_splitter.addWidget(playback_control)

        left_splitter.setSizes([400, 160, 160, 80])

        # ==== RIGHT COL ====
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Box 1: Frame Display
        self.scroll_area = QScrollArea()
        self.video_frame = QLabel("Frame Display Area")
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.video_frame)
        right_splitter.addWidget(self.scroll_area)
        
        # Box 2: Timeline Bar
        self.timeline_bar = QLabel("Timeline Bar")
        self.timeline_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_splitter.addWidget(self.timeline_bar)
        
        # Initial stretch factors (3:1)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)
        
        # ==== COMBINE COLS ====
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])

        # Main layout
        layout = QHBoxLayout(self.central_widget)
        layout.addWidget(main_splitter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Style
        self.setStyleSheet("""
            QFrame, QTextEdit, QLabel {
                border: 1px solid #555;
                background: #222;
                color: white;
            }
            QSplitter::handle {
                background: #444;
                width: 2px;
                height: 2px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MP4Analyzer()
    window.show()
    sys.exit(app.exec())
