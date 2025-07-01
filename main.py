import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

class MP4AnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Analyzer 🎥")
        self.setMinimumSize(1000, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top: Frame display placeholder
        self.video_frame = QLabel("Frame Display Area")
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.video_frame.setFixedHeight(500)

        # Bottom: Timeline placeholder
        self.timeline = QLabel("Timeline Bar (To Be Implemented)")
        self.timeline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timeline.setFixedHeight(100)
        self.timeline.setAutoFillBackground(True)

        palette = self.timeline.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#333"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        self.timeline.setPalette(palette)

        # Add to layout
        layout.addWidget(self.video_frame)
        layout.addWidget(self.timeline)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MP4AnalyzerApp()
    window.show()
    sys.exit(app.exec())