import sys
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QFrame, QScrollArea, QTextEdit, QSlider,
    QSplitter, QFileDialog
)
from loadmp4.load import MP4Loader, VideoInfo

class MP4Analyzer(QMainWindow):
    """
    Main application window for the MP4 Analyzer GUI.
    Sets up the menu, UI components, and handles video loading.
    """
    def __init__(self):
        super().__init__()
        self.current_video: Optional[VideoInfo] = None

        # Window setup
        self.setWindowTitle("MP4 Analyzer")
        self.setMinimumSize(1200, 800)

        # Central widget to hold splitters
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize UI and menu
        self._init_ui()
        self._init_menu()

    def _init_menu(self):
        """
        Initializes the menu bar with File->Open action.
        """
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        open_action = file_menu.addAction("Open MP4...")
        open_action.triggered.connect(self._open_file_dialog)

    def _open_file_dialog(self):
        """
        Opens a file dialog to select an MP4 file and loads it.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open MP4 File",
            "",
            "MP4 Files (*.mp4 *.mov);;All Files (*)"
        )
        if file_path:
            self._load_video(file_path)

    def _load_video(self, file_path: str):
        """
        Uses MP4Loader to load the video metadata and updates UI.

        Parameters:
            file_path: Path to the video file to load.
        """
        self.current_video = MP4Loader.load_video(file_path)
        if self.current_video:
            self._update_ui_with_video_info()
        else:
            self.log_box.append(f"❌ Failed to load: {file_path}")

    def _update_ui_with_video_info(self):
        """
        Displays the loaded video's metadata in the metadata box and logs success.
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
        self.log_box.append(f"✅ Loaded: {self.current_video.path}")

    def _init_ui(self):
        """
        Sets up the main splitter layout with left and right panels.
        """
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Build and add left/right panels
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])

        # Apply to central widget
        layout = QHBoxLayout(self.central_widget)
        layout.addWidget(main_splitter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Global styling
        self.setStyleSheet("""
            QFrame, QTextEdit, QLabel {
                border: 1px solid #555;
                background: #222;
                color: white;
            }
            QSplitter::handle {
                background: #444;
                width: 2px; height: 2px;
            }
        """)

    def _create_left_panel(self) -> QSplitter:
        """
        Creates the left vertical splitter containing metadata, filters, log, and playback control widgets.

        Returns:
            Configured QSplitter with the left-side panels.
        """
        left_splitter = QSplitter(Qt.Orientation.Vertical)

        # Metadata, Filters, Log: simple read-only text boxes
        self.metadata_box = self._create_text_box("MP4 Metadata")
        left_splitter.addWidget(self.metadata_box)

        self.filters_box = self._create_text_box("Sequences/Filters")
        left_splitter.addWidget(self.filters_box)

        self.log_box = self._create_text_box("Log Messages")
        left_splitter.addWidget(self.log_box)

        # Playback controls panel
        playback_control = self._create_playback_control()
        left_splitter.addWidget(playback_control)

        # Initial splitter sizes
        left_splitter.setSizes([400, 160, 160, 80])
        return left_splitter

    def _create_right_panel(self) -> QSplitter:
        """
        Creates the right vertical splitter containing the frame display area and timeline bar.

        Returns:
            Configured QSplitter with the right-side panels.
        """
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Frame display inside scroll area
        self.scroll_area = QScrollArea()
        self.video_frame = QLabel("Frame Display Area")
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.video_frame)
        right_splitter.addWidget(self.scroll_area)

        # Timeline bar placeholder
        self.timeline_bar = QLabel("Timeline Bar")
        self.timeline_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_splitter.addWidget(self.timeline_bar)

        # Set stretch: display bigger than timeline
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)
        return right_splitter

    def _create_text_box(self, placeholder: str) -> QTextEdit:
        """
        Helper to create a read-only QTextEdit with a placeholder text.

        Parameters:
            placeholder: Placeholder text when the box is empty.
        Returns:
            Configured QTextEdit widget.
        """
        box = QTextEdit()
        box.setReadOnly(True)
        box.setPlaceholderText(placeholder)
        return box

    def _create_playback_control(self) -> QFrame:
        """
        Constructs the playback control panel with a slider, frame counter, and navigation buttons.

        Returns:
            Configured QFrame containing playback controls.
        """
        frame = QFrame()
        layout = QVBoxLayout(frame)

        # Title label
        title = QLabel("Playback Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; border: none;")
        layout.addWidget(title)

        # Slider widget
        self.playback_slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.playback_slider)

        # Bottom row container
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Frame counter label
        self.frame_counter_label = QLabel("0 / 0")
        self.frame_counter_label.setFixedSize(80, 25)
        self.frame_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.frame_counter_label, alignment=Qt.AlignmentFlag.AlignLeft)

        # Navigation buttons
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 2, 0)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.prev_button = QLabel("<")
        self.next_button = QLabel(">")
        for btn in (self.prev_button, self.next_button):
            btn.setFixedSize(40, 25)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setStyleSheet("border: 1px solid #555; background: #333;")
            nav_layout.addWidget(btn)
        bottom_layout.addWidget(nav_container)

        layout.addWidget(bottom_row)
        return frame

if __name__ == "__main__":
    # Entrypoint: create application and run main window
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MP4Analyzer()
    window.show()
    sys.exit(app.exec())
