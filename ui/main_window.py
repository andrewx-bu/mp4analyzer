# Main window for MP4 Analyzer application.
from typing import Optional
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from models import VideoMetadata, LazyVideoFrameCollection
from video_loader import VideoLoader, VideoLoaderError
from ui.ui_components import (
    create_main_layout,
    PlaybackControlWidget,
    LeftPanelWidget,
    RightPanelWidget,
)
from src.mp4analyzer import parse_mp4_boxes, generate_movie_info


class MP4AnalyzerMainWindow(QMainWindow):
    """Main window for the MP4 Analyzer application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Analyzer")
        self.setMinimumSize(1200, 800)

        # Application state
        self._video_metadata: Optional[VideoMetadata] = None
        self._frame_collection = LazyVideoFrameCollection("", [], [])
        self._current_frame_index = 0
        self._zoom_factor = 1.0
        self._video_loader = VideoLoader()
        self._last_display_log_index: Optional[int] = None

        # UI components
        self._playback_control: Optional[PlaybackControlWidget] = None
        self._left_panel: Optional[LeftPanelWidget] = None
        self._right_panel: Optional[RightPanelWidget] = None

        self._setup_ui()

    def _setup_ui(self):
        """Initialize the user interface."""
        # Menu bar
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("Open MP4...", self)
        open_action.triggered.connect(self._handle_open_file)
        file_menu.addAction(open_action)

        # Main layout
        main_splitter, playback_control, left_panel, right_panel = create_main_layout(
            on_open_file=self._handle_open_file,
            on_save_snapshot=self._handle_save_snapshot,
            on_reset_zoom=self._handle_reset_zoom,
            on_zoom_changed=self._handle_zoom_changed,
            on_frame_changed=self._handle_frame_changed,
            on_frame_selected=self._handle_frame_selected,
        )

        self._playback_control = playback_control
        self._left_panel = left_panel
        self._right_panel = right_panel
        self.setCentralWidget(main_splitter)

        # Navigation buttons
        self._playback_control.previous_button.clicked.connect(
            lambda: self._navigate_frame(-1)
        )
        self._playback_control.next_button.clicked.connect(
            lambda: self._navigate_frame(1)
        )

        # Event filters for zoom
        self._right_panel.video_canvas.installEventFilter(self)
        self._right_panel.video_canvas.video_label.installEventFilter(self)

        # Styling
        self.setStyleSheet(
            """
            QFrame, QTextEdit, QLabel, QPushButton {
                border: 1px solid #555; background: #222; color: white;
            }
            QSplitter::handle { background: #444; width: 2px; height: 2px; }
        """
        )

    def _handle_open_file(self):
        """Handle file open requests."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open MP4 File", "", "MP4 Files (*.mp4 *.mov);;All Files (*)"
        )
        if file_path:
            self._load_video_file(file_path)

    def _load_video_file(self, file_path: str):
        """Load and process a video file."""
        try:
            self._log_message(f"Loading video file: {file_path}")

            metadata, frame_collection = self._video_loader.load_video_file(
                file_path, log_callback=self._log_message
            )

            if not metadata:
                self._log_message(f"❌ Failed to load metadata: {file_path}")
                QMessageBox.critical(
                    self,
                    "Failed to load video",
                    "Could not extract metadata from the selected file.",
                )
                return

            self._video_metadata = metadata
            self._frame_collection = frame_collection
            self._current_frame_index = 0
            self._last_display_log_index = None

            # Parse MP4 boxes and detailed metadata
            try:
                boxes = parse_mp4_boxes(file_path)
            except Exception as ex:
                self._log_message(f"Failed to parse boxes: {ex}")
                boxes = []

            try:
                metadata_text = generate_movie_info(file_path, boxes)
            except Exception as ex:
                metadata_text = f"Failed to extract metadata: {ex}"

            self._left_panel.update_metadata(metadata_text)
            self._left_panel.update_boxes(boxes)
            self._playback_control.set_frame_range(frame_collection.count)
            self._right_panel.timeline_widget.set_frame_data(
                frame_collection.frame_metadata_list
            )
            self._display_current_frame()

            self._log_message(
                f"✅ Loaded: {file_path} ({frame_collection.count} frames)"
            )

        except VideoLoaderError as e:
            self._log_message(f"❌ {str(e)}")
            QMessageBox.critical(self, "Video Loading Error", str(e))
        except Exception as e:
            self._log_message(f"❌ Unexpected error: {str(e)}")
            QMessageBox.critical(
                self, "Unexpected Error", f"An unexpected error occurred: {str(e)}"
            )

    def _handle_save_snapshot(self):
        """Handle snapshot save requests."""
        if self._frame_collection.is_empty:
            QMessageBox.warning(
                self, "No Video Loaded", "Please load a video file first."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Snapshot", "", "PNG Files (*.png)"
        )
        if file_path:
            try:
                pixmap = self._right_panel.video_canvas.video_label.pixmap()
                if pixmap and not pixmap.isNull():
                    pixmap.save(file_path, "PNG")
                    self._log_message(f"✅ Snapshot saved: {file_path}")
                else:
                    self._log_message("❌ No image to save")
            except Exception as e:
                self._log_message(f"❌ Error saving snapshot: {str(e)}")
                QMessageBox.critical(
                    self, "Save Error", f"Failed to save snapshot: {str(e)}"
                )

    def _handle_frame_changed(self, frame_index: int):
        self._display_frame(frame_index)

    def _handle_frame_selected(self, frame_index: int):
        self._display_frame(frame_index)
        frame_meta = self._frame_collection.get_frame_metadata(frame_index)
        if frame_meta:
            self._log_message(
                f"Frame {frame_index}: {frame_meta.size_bytes} bytes, "
                f"PTS {frame_meta.pts}, Decode {frame_meta.decode_order}, "
                f"TS {frame_meta.timestamp:.3f}, "
                f"Ref prev={frame_meta.ref_prev}, next={frame_meta.ref_next}"
            )

    def _navigate_frame(self, offset: int):
        self._display_frame(self._current_frame_index + offset)

    def _display_frame(self, frame_index: int):
        """Display a specific frame."""
        if self._frame_collection.is_empty:
            return

        valid_index = self._frame_collection.get_valid_index(frame_index)
        frame_meta = self._frame_collection.get_frame_metadata(valid_index)
        frame = self._frame_collection.get_frame(valid_index)

        if not frame:
            return

        # Apply zoom and display
        pixmap = QPixmap.fromImage(frame)
        if self._zoom_factor != 1.0:
            new_width = int(pixmap.width() * self._zoom_factor)
            new_height = int(pixmap.height() * self._zoom_factor)
            pixmap = pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self._right_panel.video_canvas.display_frame(pixmap)
        self._current_frame_index = valid_index

        if self._last_display_log_index != valid_index:
            if frame_meta:
                self._log_message(
                    f"➡️ Frame {valid_index} ({frame_meta.frame_type}, {frame_meta.size_bytes}B)"
                )
            else:
                self._log_message(f"➡️ Frame {valid_index}")
            self._last_display_log_index = valid_index

        # Update UI
        self._playback_control.set_current_frame(
            valid_index, self._frame_collection.count
        )
        self._right_panel.timeline_widget.set_selected_frame(valid_index)
        self._right_panel.control_bar.set_resolution_text(
            f"{frame.width()}x{frame.height()}"
        )

    def _display_current_frame(self):
        self._display_frame(self._current_frame_index)

    def _handle_zoom_changed(self, zoom_percent: int):
        self._zoom_factor = zoom_percent / 100.0
        self._display_current_frame()

    def _handle_reset_zoom(self):
        self._right_panel.control_bar.reset_zoom_value()

    def _log_message(self, message: str):
        if self._left_panel:
            self._left_panel.add_log_message(message)

    def eventFilter(self, source, event):
        """Handle mouse wheel zoom."""
        if event.type() == QEvent.Type.Wheel and source in (
            self._right_panel.video_canvas,
            self._right_panel.video_canvas.video_label,
        ):
            current_zoom = self._right_panel.control_bar.current_zoom_percent
            steps = 2 if event.angleDelta().y() > 0 else -2
            new_zoom = max(1, min(500, current_zoom + steps))
            self._right_panel.control_bar.zoom_spinbox.setValue(new_zoom)
            return True
        return super().eventFilter(source, event)
