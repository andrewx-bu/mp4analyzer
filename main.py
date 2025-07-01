import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QScrollArea, QTextEdit, QSlider, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt

class MP4AnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Analyzer")
        self.setMinimumSize(1200, 800)
        self.init_ui()

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
        self.playback_slider = QSlider(Qt.Orientation.Horizontal)
        playback_layout.addWidget(self.playback_slider)
        playback_control.setLayout(playback_layout)
        left_splitter.addWidget(playback_control)
        
        # Initial stretch factors (5:2:2:1)
        left_splitter.setStretchFactor(0, 5)
        left_splitter.setStretchFactor(1, 2)
        left_splitter.setSizes([400, 160, 160, 80])  # Initial pixel sizes
        
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
        
        # Allow left col to collapse
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(main_splitter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Style
        self.setStyleSheet("""
            QFrame, QTextEdit, QLabel {
                border: 1px solid #555;
                background: #222;
                color: white;
            }
            QSplitter::handle {
                background: #444;
                width: 4px;
                height: 4px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MP4AnalyzerApp()
    window.show()
    sys.exit(app.exec())