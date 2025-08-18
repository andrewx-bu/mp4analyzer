# Main window for MP4 Analyzer application.
from typing import Optional
from PyQt6.QtCore import Qt, QEvent, QThread, pyqtSignal, QThreadPool, QRunnable, QObject
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QProgressDialog
import concurrent.futures
from models import VideoMetadata, LazyVideoFrameCollection
from video_loader import VideoLoader, VideoLoaderError
from ui.ui_components import (
    create_main_layout,
    PlaybackControlWidget,
    LeftPanelWidget,
    RightPanelWidget,
)
from src.mp4analyzer import parse_mp4_boxes, generate_movie_info


class FrameLoaderSignals(QObject):
    """Signals for frame loading workers."""
    frame_loaded = pyqtSignal(int, object)  # index, QImage

class FrameLoaderWorker(QRunnable):
    """Worker for loading individual frames."""
    def __init__(self, frame_collection, index, signals):
        super().__init__()
        self.frame_collection = frame_collection
        self.index = index
        self.signals = signals
        
    def run(self):
        """Load frame in background."""
        if self.frame_collection and not self.frame_collection.is_empty:
            frame = self.frame_collection.get_frame(self.index)
            if frame:
                self.signals.frame_loaded.emit(self.index, frame)

class FrameLoaderThread(QThread):
    """Background thread pool manager for frame loading."""
    frame_loaded = pyqtSignal(int, object)  # index, QImage
    
    def __init__(self, frame_collection):
        super().__init__()
        self.frame_collection = frame_collection
        self.requested_frames = []
        self._running = True
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(3)  # Limit concurrent decoding
        self.signals = FrameLoaderSignals()
        self.signals.frame_loaded.connect(self.frame_loaded.emit)
        
    def request_frame(self, index: int):
        """Request frame loading in background."""
        if index not in self.requested_frames:
            self.requested_frames.append(index)
    
    def stop(self):
        """Stop the thread gracefully."""
        self._running = False
        self.thread_pool.waitForDone(1000)  # Wait up to 1 second
        self.quit()
        self.wait()
    
    def run(self):
        """Background frame loading loop with thread pool."""
        while self._running:
            if not self.requested_frames:
                self.msleep(50)  # Wait 50ms before checking again
                continue
                
            index = self.requested_frames.pop(0)
            worker = FrameLoaderWorker(self.frame_collection, index, self.signals)
            self.thread_pool.start(worker)


class VideoLoadWorker(QThread):
    """Background thread for video loading."""
    video_loaded = pyqtSignal(object, object)  # metadata, frame_collection
    loading_progress = pyqtSignal(str)  # progress message
    loading_error = pyqtSignal(str)  # error message
    
    def __init__(self, file_path, video_loader):
        super().__init__()
        self.file_path = file_path
        self.video_loader = video_loader
        
    def run(self):
        """Load video in background."""
        try:
            self.loading_progress.emit("Loading video metadata...")
            metadata, frame_collection = self.video_loader.load_video_file(self.file_path)
            self.video_loaded.emit(metadata, frame_collection)
        except VideoLoaderError as e:
            self.loading_error.emit(str(e))
        except Exception as e:
            self.loading_error.emit(f"Unexpected error: {str(e)}")


class MP4AnalyzerMainWindow(QMainWindow):
    """Main window for the MP4 Analyzer application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Analyzer")
        self.setMinimumSize(1200, 800)

        # Application state
        self._video_metadata: Optional[VideoMetadata] = None
        self._frame_collection = LazyVideoFrameCollection("", [], [])  # empty init
        self._current_frame_index = 0
        self._zoom_factor = 1.0
        self._video_loader = VideoLoader()
        self._last_display_log_index: Optional[int] = None
        self._frame_loader_thread: Optional[FrameLoaderThread] = None
        self._video_load_worker: Optional[VideoLoadWorker] = None
        self._progress_dialog: Optional[QProgressDialog] = None

        # UI components
        self._playback_control: Optional[PlaybackControlWidget] = None
        self._left_panel: Optional[LeftPanelWidget] = None
        self._right_panel: Optional[RightPanelWidget] = None

        # Build interface
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the main user interface: menu, panels, styling."""
        # --- Menu bar ---
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("Open MP4...", self)
        open_action.triggered.connect(self._handle_open_file)
        file_menu.addAction(open_action)

        # --- Main layout (splitter + panels) ---
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

        # --- Navigation buttons ---
        self._playback_control.previous_button.clicked.connect(
            lambda: self._navigate_frame(-1)
        )
        self._playback_control.next_button.clicked.connect(
            lambda: self._navigate_frame(1)
        )

        # --- Zoom controls via mouse wheel ---
        self._right_panel.video_canvas.installEventFilter(self)
        self._right_panel.video_canvas.video_label.installEventFilter(self)

        # --- Dark styling ---
        self.setStyleSheet(
            """
            QFrame, QTextEdit, QLabel, QPushButton {
                border: 1px solid #555; background: #222; color: white;
            }
            QSplitter::handle { background: #444; width: 2px; height: 2px; }
        """
        )

    def _handle_open_file(self):
        """Prompt user to select a video file to load."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open MP4 File", "", "MP4 Files (*.mp4 *.mov);;All Files (*)"
        )
        if file_path:
            self._load_video_file(file_path)

    def _load_video_file(self, file_path: str):
        """Load a video file asynchronously to prevent UI freezing."""
        # Stop existing workers
        if self._frame_loader_thread:
            self._frame_loader_thread.stop()
            self._frame_loader_thread = None
        if self._video_load_worker:
            self._video_load_worker.quit()
            self._video_load_worker.wait()

        # Show progress dialog
        self._progress_dialog = QProgressDialog("Loading video file...", "Cancel", 0, 0, self)
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setMinimumDuration(500)  # Show after 500ms
        self._progress_dialog.show()

        # Start async video loading
        self._video_load_worker = VideoLoadWorker(file_path, self._video_loader)
        self._video_load_worker.video_loaded.connect(self._on_video_loaded)
        self._video_load_worker.loading_progress.connect(self._on_loading_progress)
        self._video_load_worker.loading_error.connect(self._on_loading_error)
        self._video_load_worker.start()

    def _on_video_loaded(self, metadata, frame_collection):
        """Handle video loaded from background thread."""
        self._video_metadata = metadata
        self._frame_collection = frame_collection
        
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        if self._video_metadata and not self._frame_collection.is_empty:
            self._current_frame_index = 0
            
            # Start frame loader thread
            self._frame_loader_thread = FrameLoaderThread(self._frame_collection)
            self._frame_loader_thread.frame_loaded.connect(self._on_frame_loaded)
            self._frame_loader_thread.start()
            
            self._update_ui_for_loaded_video()
            self._display_current_frame()
        else:
            QMessageBox.warning(
                self, "Load Error", "Failed to load video metadata or frames."
            )

    def _on_loading_progress(self, message: str):
        """Update progress dialog with loading status."""
        if self._progress_dialog:
            self._progress_dialog.setLabelText(message)

    def _on_loading_error(self, error_message: str):
        """Handle video loading error."""
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
        QMessageBox.critical(self, "Video Load Error", error_message)

    def _on_frame_loaded(self, index: int, frame):
        """Handle frame loaded from background thread."""
        # Only update display if this is the current frame
        if index == self._current_frame_index:
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

    def _update_ui_for_loaded_video(self):
        """Update UI components after video is loaded."""
        if not self._video_metadata or self._frame_collection.is_empty:
            return

        # Parse MP4 boxes and metadata text
        try:
            boxes = parse_mp4_boxes(self._frame_collection._file_path)
        except Exception as ex:
            self._log_message(f"Failed to parse boxes: {ex}")
            boxes = []

        try:
            metadata_text = generate_movie_info(self._frame_collection._file_path, boxes)
        except Exception as ex:
            metadata_text = f"Failed to extract metadata: {ex}"

        # Update UI panels with metadata and boxes
        self._left_panel.update_metadata(metadata_text)
        self._left_panel.update_boxes(boxes)
        self._playback_control.set_frame_range(self._frame_collection.count)
        self._right_panel.timeline_widget.set_frame_data(
            self._frame_collection.frame_metadata_list
        )

        self._log_message(
            f"✅ Loaded: {self._frame_collection._file_path} ({self._frame_collection.count} frames)"
        )

    def _handle_save_snapshot(self):
        """Prompt user to save current video frame as PNG snapshot."""
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
        """Triggered when timeline slider is moved."""
        self._display_frame(frame_index)

    def _handle_frame_selected(self, frame_index: int):
        """Triggered when a frame is selected on the timeline."""
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
        """Move relative to current frame (prev/next)."""
        self._display_frame(self._current_frame_index + offset)

    def _display_frame(self, frame_index: int):
        """Decode and display a specific frame at given index."""
        if self._frame_collection.is_empty:
            return

        # Clamp frame index
        valid_index = self._frame_collection.get_valid_index(frame_index)
        self._current_frame_index = valid_index
        
        # Update UI immediately for responsiveness
        self._playback_control.set_current_frame(
            valid_index, self._frame_collection.count
        )
        self._right_panel.timeline_widget.set_selected_frame(valid_index)
        
        # Try to get frame from cache first (fast path)
        with self._frame_collection._lock:
            cached_frame = self._frame_collection._cache.get(valid_index)
        
        if cached_frame:
            # Frame in uncompressed cache - display immediately
            self._display_frame_image(cached_frame)
        else:
            # Try compressed cache (medium speed)
            compressed_frame = self._frame_collection._load_from_compressed_cache(valid_index)
            if compressed_frame:
                self._display_frame_image(compressed_frame)
            else:
                # Frame not cached - request async loading and show placeholder
                if self._frame_loader_thread:
                    self._frame_loader_thread.request_frame(valid_index)
                # Keep previous frame displayed until new one loads

        # Log and preload in background
        frame_meta = self._frame_collection.get_frame_metadata(valid_index)
        if self._last_display_log_index != valid_index:
            if frame_meta:
                self._log_message(
                    f"➡️ Frame {valid_index} ({frame_meta.frame_type}, {frame_meta.size_bytes}B)"
                )
            else:
                self._log_message(f"➡️ Frame {valid_index}")
            self._last_display_log_index = valid_index
        
        # Preload nearby frames for smoother navigation
        self._preload_nearby_frames(valid_index)

    def _display_frame_image(self, frame: object):
        """Display a QImage frame with zoom applied."""
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
        self._right_panel.control_bar.set_resolution_text(
            f"{frame.width()}x{frame.height()}"
        )

    def _display_current_frame(self):
        """Redisplay current frame index."""
        self._display_frame(self._current_frame_index)

    def _handle_zoom_changed(self, zoom_percent: int):
        """Update zoom factor and redraw frame."""
        self._zoom_factor = zoom_percent / 100.0
        self._display_current_frame()

    def _handle_reset_zoom(self):
        """Reset zoom back to 100%."""
        self._right_panel.control_bar.reset_zoom_value()

    def _preload_nearby_frames(self, current_index: int):
        """Preload frames around current index with intelligent patterns."""
        if not self._frame_loader_thread or self._frame_collection.is_empty:
            return
        
        # Track navigation direction for smarter preloading
        if hasattr(self, '_last_frame_index'):
            direction = 1 if current_index > self._last_frame_index else -1
        else:
            direction = 1
        self._last_frame_index = current_index
        
        # Preload more frames in the direction of navigation
        if direction > 0:  # Moving forward
            preload_behind, preload_ahead = 2, 5
        else:  # Moving backward
            preload_behind, preload_ahead = 5, 2
            
        # Preload frames prioritizing navigation direction
        for offset in range(-preload_behind, preload_ahead + 1):
            target_index = current_index + offset
            if 0 <= target_index < self._frame_collection.count and target_index != current_index:
                self._frame_loader_thread.request_frame(target_index)

    def _log_message(self, message: str):
        """Forward log messages to left panel."""
        if self._left_panel:
            self._left_panel.add_log_message(message)

    def closeEvent(self, event):
        """Clean up resources when window is closed."""
        if self._frame_loader_thread:
            self._frame_loader_thread.stop()
        if self._video_load_worker:
            self._video_load_worker.quit()
            self._video_load_worker.wait()
        if self._progress_dialog:
            self._progress_dialog.close()
        super().closeEvent(event)

    def eventFilter(self, source, event):
        """Handle mouse wheel zooming on video canvas."""
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
