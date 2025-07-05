# Entry point for MP4 Analyzer application.
import sys
from typing import Optional, List
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QFileDialog
import ui
from loader import MP4Loader, VideoInfo
from timeline import FrameInfo

# Map PyAV pict_type values to frame type letters
PICT_TYPE_MAP = {
    0: '?',
    1: 'I',
    2: 'P',
    3: 'B',
    4: 'S',
    5: 'SI',
    6: 'SP',
    7: 'BI',
}

class MP4Analyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Analyzer")
        self.setMinimumSize(1200, 800)

        self.video_info: Optional[VideoInfo] = None
        self.frames: List[QImage] = []
        self.frame_info: List[FrameInfo] = []
        self.current_idx: int = 0
        self.zoom: float = 1.0

        # Build UI
        self._init_ui()
        self._init_menu()
        self.canvas.installEventFilter(self)
        self.video_lbl.installEventFilter(self)

    def _init_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("Open MP4...").triggered.connect(self._open_file)

    def _init_ui(self):
        # Main horizontal splitter between left and right panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Playback control widgets
        playback_widget, self.slider, self.prev_btn, self.next_btn, self.counter_lbl = ui.create_playback_control(
            self._display_frame)

        # Left and right panels
        self.left_panel = ui.create_left_panel(playback_widget)
        (self.canvas, self.video_lbl, self.zoom_spin, self.res_lbl,
         self.timeline, self.right_panel) = ui.create_right_panel(
            self._open_file, self._save_snapshot, self._reset_zoom, self._set_zoom,
            self._display_frame)

        # Add panels to splitter
        main_splitter.addWidget(self.left_panel)
        main_splitter.addWidget(self.right_panel)
        main_splitter.setSizes([int(self.width()*0.2), int(self.width()*0.8)])

        # Set central widget
        self.setCentralWidget(main_splitter)

        # Connect navigation
        self.prev_btn.clicked.connect(lambda: self._step(-1))
        self.next_btn.clicked.connect(lambda: self._step(1))

        # Style
        self.setStyleSheet("""
            QFrame, QTextEdit, QLabel, QPushButton { border: 1px solid #555; background: #222; color: white; }
            QSplitter::handle { background: #444; width:2px; height:2px; }
        """)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open MP4 File", "", "MP4 Files (*.mp4 *.mov);;All Files (*)"
        )
        if path:
            self._load(path)

    def _load(self, path: str):
        # Metadata
        self.video_info = MP4Loader.load_video(path)
        if not self.video_info:
            self._log(f"❌ Failed to load metadata: {path}")
            return

        self._update_metadata()

        # Decode all frames and gather info
        try:
            import av
            container = av.open(path)
            stream = next(s for s in container.streams if s.type == 'video')
            self.frames = []
            self.frame_info = []
            for packet in container.demux(stream):
                for f in packet.decode():
                    img = QImage(
                        f.to_ndarray(format='rgb24').data,
                        f.width,
                        f.height,
                        QImage.Format.Format_RGB888,
                    ).copy()
                    self.frames.append(img)
                    ftype = PICT_TYPE_MAP.get(getattr(f, 'pict_type', 0), '?')
                    self.frame_info.append(FrameInfo(size=getattr(packet, 'size', 0), ftype=ftype))
        except Exception as e:
            self._log(f"❌ Error decoding: {e}")
            return

        total = len(self.frames)
        self.slider.setRange(0, max(0, total-1))
        self.slider.setValue(0)
        if hasattr(self, 'timeline'):
            self.timeline.set_frames(self.frame_info)
        self._display_frame(0)
        self._log(f"✅ Loaded: {path} ({total} frames)")

    def _update_metadata(self):
        info = self.video_info
        text = (
            f"=== Video Metadata ===\n"
            f"Path: {info.path}\n"
            f"Resolution: {info.width}x{info.height}\n"
            f"Codec: {info.codec}\n"
            f"FPS: {info.fps:.2f}\n"
            f"Duration: {info.duration:.2f}s\n"
            f"Frames: {info.frame_count}\n"
        )
        self.left_panel.widget(0).setPlainText(text)

    def _display_frame(self, idx: int):
        if not self.frames:
            return
        idx = max(0, min(idx, len(self.frames)-1))
        img = self.frames[idx]
        pix = QPixmap.fromImage(img)

        # Zoom
        w = int(img.width() * self.zoom)
        h = int(img.height() * self.zoom)
        scaled = pix.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.canvas.set_pixmap(scaled)

        self.current_idx = idx
        self.counter_lbl.setText(f"{idx+1} / {len(self.frames)}")
        if self.slider.value() != idx:
            self.slider.blockSignals(True)
            self.slider.setValue(idx)
            self.slider.blockSignals(False)

        if hasattr(self, 'timeline'):
            self.timeline.set_selected(idx)

        self.res_lbl.setText(f"{img.width()}x{img.height()}")

    def _step(self, offset: int):
        self._display_frame(self.current_idx + offset)

    def _save_snapshot(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Snapshot", "", "PNG Files (*.png)"
        )
        if path:
            self.video_lbl.pixmap().save(path, "PNG")
            self._log(f"✅ Snapshot saved: {path}")

    def _reset_zoom(self):
        self.zoom_spin.setValue(100)

    def _set_zoom(self, percent: int):
        self.zoom = percent / 100.0
        self._display_frame(self.current_idx)

    def _log(self, message: str):
        self.left_panel.widget(2).append(message)

    def eventFilter(self, source, event):
        if source in (self.canvas, self.video_lbl) and event.type() == QEvent.Type.Wheel:
            step = 2 if event.angleDelta().y() > 0 else -2
            self.zoom_spin.setValue(
                max(self.zoom_spin.minimum(), min(self.zoom_spin.maximum(), self.zoom_spin.value() + step))
            )
            return True
        return super().eventFilter(source, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MP4Analyzer()
    window.show()
    sys.exit(app.exec())