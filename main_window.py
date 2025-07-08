# Main window for MP4 Analyzer application.
from typing import Optional
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from models import VideoMetadata, LazyVideoFrameCollection
from video_loader import VideoLoader, VideoLoaderError
from ui_components import create_main_layout, PlaybackControlWidget, LeftPanelWidget, RightPanelWidget


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
        
        # Core components
        self._video_loader = VideoLoader()
        
        # UI components (will be set in _initialize_ui)
        self._playback_control: Optional[PlaybackControlWidget] = None
        self._left_panel: Optional[LeftPanelWidget] = None
        self._right_panel: Optional[RightPanelWidget] = None
        
        self._initialize_ui()
        self._setup_event_filters()
        self._apply_application_styling()
    
    def _initialize_ui(self):
        """Initialize the user interface."""
        self._setup_menu_bar()
        self._setup_main_layout()
    
    def _setup_menu_bar(self):
        """Create and configure the menu bar."""
        file_menu = self.menuBar().addMenu("&File")
        
        open_action = QAction("Open MP4...", self)
        open_action.triggered.connect(self._handle_open_file)
        file_menu.addAction(open_action)
    
    def _setup_main_layout(self):
        """Create and configure the main layout."""
        main_splitter, playback_control, left_panel, right_panel = create_main_layout(
            on_open_file=self._handle_open_file,
            on_save_snapshot=self._handle_save_snapshot,
            on_reset_zoom=self._handle_reset_zoom,
            on_zoom_changed=self._handle_zoom_changed,
            on_frame_changed=self._handle_frame_changed,
            on_frame_selected=self._handle_frame_selected
        )
        
        # Store references to components
        self._playback_control = playback_control
        self._left_panel = left_panel
        self._right_panel = right_panel
        
        # Set central widget
        self.setCentralWidget(main_splitter)
        
        # Connect navigation buttons
        self._connect_navigation_buttons()
    
    def _connect_navigation_buttons(self):
        """Connect navigation button signals."""
        self._playback_control.previous_button.clicked.connect(
            lambda: self._navigate_frame(-1)
        )
        self._playback_control.next_button.clicked.connect(
            lambda: self._navigate_frame(1)
        )
    
    def _setup_event_filters(self):
        """Setup event filters for mouse wheel zoom."""
        self._right_panel.video_canvas.installEventFilter(self)
        self._right_panel.video_canvas.video_label.installEventFilter(self)
    
    def _apply_application_styling(self):
        """Apply consistent styling to the application."""
        self.setStyleSheet("""
            QFrame, QTextEdit, QLabel, QPushButton {
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
    
    # File operations
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
            
            # Load video metadata and frames
            metadata, frame_collection = self._video_loader.load_video_file(
                file_path,
                log_callback=self._log_message
            )
            
            if not metadata:
                self._log_message(f"❌ Failed to load metadata: {file_path}")
                self._show_error_message("Failed to load video file", 
                                       "Could not extract metadata from the selected file.")
                return
            
            # Update application state
            self._video_metadata = metadata
            self._frame_collection = frame_collection
            self._current_frame_index = 0
            
            # Update UI
            self._update_ui_after_loading()
            
            self._log_message(f"✅ Loaded: {file_path} ({frame_collection.count} frames)")
            
        except VideoLoaderError as e:
            self._log_message(f"❌ {str(e)}")
            self._show_error_message("Video Loading Error", str(e))
        except Exception as e:
            self._log_message(f"❌ Unexpected error: {str(e)}")
            self._show_error_message("Unexpected Error", f"An unexpected error occurred: {str(e)}")
    
    def _update_ui_after_loading(self):
        """Update UI components after successfully loading a video."""
        # Update metadata display
        self._update_metadata_display()
        
        # Update playback controls
        self._playback_control.set_frame_range(self._frame_collection.count)
        
        # Update timeline
        self._right_panel.timeline_widget.set_frame_data(
            self._frame_collection.frame_metadata_list
        )
        
        # Display first frame
        self._display_current_frame()
    
    def _update_metadata_display(self):
        """Update the metadata text display."""
        if not self._video_metadata:
            return
        
        metadata_text = self._format_metadata_text(self._video_metadata)
        self._left_panel.update_metadata(metadata_text)
    
    def _format_metadata_text(self, metadata: VideoMetadata) -> str:
        """Format metadata for display."""
        return (
            f"=== Video Metadata ===\n"
            f"Path: {metadata.file_path}\n"
            f"Resolution: {metadata.resolution_text}\n"
            f"Codec: {metadata.codec_name}\n"
            f"FPS: {metadata.frames_per_second:.2f}\n"
            f"Duration: {metadata.duration_text}\n"
            f"Frames: {metadata.total_frames}\n"
        )
    
    def _handle_save_snapshot(self):
        """Handle snapshot save requests."""
        if self._frame_collection.is_empty:
            self._show_warning_message("No Video Loaded", "Please load a video file first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Snapshot", "", "PNG Files (*.png)"
        )
        
        if file_path:
            try:
                # Get current pixmap and save
                pixmap = self._right_panel.video_canvas.video_label.pixmap()
                if pixmap and not pixmap.isNull():
                    pixmap.save(file_path, "PNG")
                    self._log_message(f"✅ Snapshot saved: {file_path}")
                else:
                    self._log_message("❌ No image to save")
            except Exception as e:
                self._log_message(f"❌ Error saving snapshot: {str(e)}")
                self._show_error_message("Save Error", f"Failed to save snapshot: {str(e)}")
    
    # Frame navigation and display
    def _handle_frame_changed(self, frame_index: int):
        """Handle frame change requests from UI controls."""
        self._display_frame(frame_index)
    
    def _handle_frame_selected(self, frame_index: int):
        """Handle frame selection from timeline."""
        self._display_frame(frame_index)
    
    def _navigate_frame(self, offset: int):
        """Navigate by a frame offset."""
        new_index = self._current_frame_index + offset
        self._display_frame(new_index)
    
    def _display_frame(self, frame_index: int):
        """Display a specific frame."""
        if self._frame_collection.is_empty:
            return
        
        # Ensure valid index
        valid_index = self._frame_collection.get_valid_index(frame_index)
        frame_meta = self._frame_collection.get_frame_metadata(valid_index)
        frame = self._frame_collection.get_frame(valid_index)
        
        if not frame:
            return
        
        # Create pixmap and apply zoom
        pixmap = QPixmap.fromImage(frame)
        scaled_pixmap = self._apply_zoom_to_pixmap(pixmap)
        
        # Update display
        self._right_panel.video_canvas.display_frame(scaled_pixmap)
        
        # Update state and UI
        self._current_frame_index = valid_index
        if frame_meta:
            self._log_message(
                f"➡️ Frame {valid_index} ({frame_meta.frame_type}, {frame_meta.size_bytes} bytes)"
            )
        self._update_frame_display_info(valid_index, frame)
    
    def _display_current_frame(self):
        """Display the current frame."""
        self._display_frame(self._current_frame_index)
    
    def _apply_zoom_to_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """Apply current zoom factor to a pixmap."""
        if self._zoom_factor == 1.0:
            return pixmap
        
        new_width = int(pixmap.width() * self._zoom_factor)
        new_height = int(pixmap.height() * self._zoom_factor)
        
        return pixmap.scaled(
            new_width, new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def _update_frame_display_info(self, frame_index: int, frame):
        """Update frame-related display information."""
        # Update playback control
        self._playback_control.set_current_frame(frame_index, self._frame_collection.count)
        
        # Update timeline selection
        self._right_panel.timeline_widget.set_selected_frame(frame_index)
        
        # Update resolution display
        self._right_panel.control_bar.set_resolution_text(f"{frame.width()}x{frame.height()}")
    
    # Zoom operations
    def _handle_zoom_changed(self, zoom_percent: int):
        """Handle zoom change from UI controls."""
        self._zoom_factor = zoom_percent / 100.0
        self._display_current_frame()
    
    def _handle_reset_zoom(self):
        """Handle zoom reset requests."""
        self._right_panel.control_bar.reset_zoom_value()
    
    def _adjust_zoom_by_steps(self, steps: int):
        """Adjust zoom by a number of steps."""
        current_zoom = self._right_panel.control_bar.current_zoom_percent
        new_zoom = current_zoom + (steps * 2)  # 2% per step
        
        # Clamp to valid range
        new_zoom = max(1, min(500, new_zoom))
        
        # Update zoom spinbox (this will trigger zoom change)
        self._right_panel.control_bar.zoom_spinbox.setValue(new_zoom)
    
    # Logging and messaging
    def _log_message(self, message: str):
        """Add a message to the log."""
        if self._left_panel:
            self._left_panel.add_log_message(message)
    
    def _show_error_message(self, title: str, message: str):
        """Show an error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def _show_warning_message(self, title: str, message: str):
        """Show a warning message dialog."""
        QMessageBox.warning(self, title, message)
    
    # Event handling
    def eventFilter(self, source, event):
        """Handle events from monitored widgets."""
        if event.type() == QEvent.Type.Wheel:
            if source in (self._right_panel.video_canvas, self._right_panel.video_canvas.video_label):
                # Handle mouse wheel zoom
                wheel_delta = event.angleDelta().y()
                zoom_steps = 2 if wheel_delta > 0 else -2
                self._adjust_zoom_by_steps(zoom_steps)
                return True
        
        return super().eventFilter(source, event)