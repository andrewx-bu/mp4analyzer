# UI component builders for MP4 Analyzer application.
from typing import Callable, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QTextEdit, QLabel, QVBoxLayout, QHBoxLayout,
    QSplitter, QWidget, QSlider, QPushButton, QSpinBox, QSizePolicy,
    QScrollArea
)
from video_canvas import VideoDisplayCanvas
from timeline_widget import TimelineBarGraph


class TextDisplayBox(QTextEdit):
    """A read-only text display widget with consistent styling."""
    
    def __init__(self, placeholder_text: str = ""):
        super().__init__()
        self.setReadOnly(True)
        if placeholder_text:
            self.setPlaceholderText(placeholder_text)


class PlaybackControlWidget(QFrame):
    """Widget containing playback controls: slider, navigation buttons, and frame counter."""
    
    def __init__(self, on_frame_changed: Callable[[int], None]):
        super().__init__()
        self.on_frame_changed = on_frame_changed
        
        # Create UI elements
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.previous_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.frame_counter_label = QLabel("0 / 0")
        
        self._setup_widget()
        self._setup_layout()
        self._connect_signals()
    
    def _setup_widget(self):
        """Configure widget properties."""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def _setup_layout(self):
        """Create and configure the layout."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Playback Control")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; border: none;")
        layout.addWidget(title_label)
        
        # Slider
        layout.addWidget(self.frame_slider)
        
        # Bottom controls
        bottom_widget = self._create_bottom_controls()
        layout.addWidget(bottom_widget)
    
    def _create_bottom_controls(self) -> QWidget:
        """Create the bottom control row with counter and navigation buttons."""
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame counter
        self.frame_counter_label.setFixedSize(80, 25)
        self.frame_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.frame_counter_label)
        
        # Navigation buttons
        nav_widget = self._create_navigation_buttons()
        bottom_layout.addWidget(nav_widget, alignment=Qt.AlignmentFlag.AlignRight)
        
        return bottom_widget
    
    def _create_navigation_buttons(self) -> QWidget:
        """Create the navigation button group."""
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 2, 0)
        
        # Style navigation buttons
        for button in [self.previous_button, self.next_button]:
            button.setFixedSize(40, 25)
            button.setStyleSheet("border: 1px solid #555; background: #333;")
        
        nav_layout.addWidget(self.previous_button)
        nav_layout.addWidget(self.next_button)
        
        return nav_widget
    
    def _connect_signals(self):
        """Connect widget signals to handlers."""
        self.frame_slider.valueChanged.connect(self.on_frame_changed)
    
    def set_frame_range(self, max_frames: int):
        """Set the range of the frame slider."""
        self.frame_slider.setRange(0, max(0, max_frames - 1))
        self.frame_slider.setValue(0)
    
    def set_current_frame(self, frame_index: int, total_frames: int):
        """Update the current frame display."""
        self.frame_counter_label.setText(f"{frame_index + 1} / {total_frames}")
        
        # Update slider without triggering signal
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(frame_index)
        self.frame_slider.blockSignals(False)


class LeftPanelWidget(QSplitter):
    """Left panel containing metadata, filters, log, and playback controls."""
    
    def __init__(self, playback_control_widget: PlaybackControlWidget):
        super().__init__(Qt.Orientation.Vertical)
        
        # Create text display boxes
        self.metadata_box = TextDisplayBox("MP4 Metadata")
        self.filters_box = TextDisplayBox("Sequences/Filters")
        self.log_box = TextDisplayBox("Log Messages")
        
        # Add widgets to splitter
        self.addWidget(self.metadata_box)
        self.addWidget(self.filters_box)
        self.addWidget(self.log_box)
        self.addWidget(playback_control_widget)
        
        # Set initial sizes
        self.setSizes([400, 160, 160, 80])
    
    def update_metadata(self, metadata_text: str):
        """Update the metadata display."""
        self.metadata_box.setPlainText(metadata_text)
    
    def add_log_message(self, message: str):
        """Add a message to the log."""
        self.log_box.append(message)


class VideoControlBar(QWidget):
    """Control bar with file operations and display settings."""
    
    def __init__(self, 
                 on_open_file: Callable,
                 on_save_snapshot: Callable,
                 on_reset_zoom: Callable,
                 on_zoom_changed: Callable[[int], None]):
        super().__init__()
        
        self.on_open_file = on_open_file
        self.on_save_snapshot = on_save_snapshot
        self.on_reset_zoom = on_reset_zoom
        self.on_zoom_changed = on_zoom_changed
        
        # Create UI elements
        self.open_button = QPushButton("Open")
        self.snapshot_button = QPushButton("Snapshot")
        self.reset_button = QPushButton("Reset")
        self.zoom_spinbox = QSpinBox()
        self.resolution_label = QLabel("--x--")
        
        self._setup_widget()
        self._setup_layout()
        self._connect_signals()
    
    def _setup_widget(self):
        """Configure widget properties."""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def _setup_layout(self):
        """Create and configure the layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File operation buttons
        self._style_button(self.open_button)
        self._style_button(self.snapshot_button)
        layout.addWidget(self.open_button)
        layout.addWidget(self.snapshot_button)
        
        # Spacer
        layout.addStretch()
        
        # Display controls
        self._style_button(self.reset_button)
        self._setup_zoom_spinbox()
        self._setup_resolution_label()
        
        layout.addWidget(self.reset_button)
        layout.addWidget(self.zoom_spinbox)
        layout.addWidget(self.resolution_label)
        
        # Align all widgets vertically
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                layout.setAlignment(item.widget(), Qt.AlignmentFlag.AlignVCenter)
    
    def _style_button(self, button: QPushButton):
        """Apply consistent styling to buttons."""
        button.setStyleSheet("padding: 3px")
    
    def _setup_zoom_spinbox(self):
        """Configure the zoom spinbox."""
        self.zoom_spinbox.setRange(1, 500)
        self.zoom_spinbox.setValue(100)
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_spinbox.setStyleSheet("padding-bottom: 1px")
    
    def _setup_resolution_label(self):
        """Configure the resolution display label."""
        self.resolution_label.setFixedSize(80, 25)
        self.resolution_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def _connect_signals(self):
        """Connect widget signals to handlers."""
        self.open_button.clicked.connect(self.on_open_file)
        self.snapshot_button.clicked.connect(self.on_save_snapshot)
        self.reset_button.clicked.connect(self.on_reset_zoom)
        self.zoom_spinbox.valueChanged.connect(self.on_zoom_changed)
    
    def set_resolution_text(self, resolution: str):
        """Update the resolution display."""
        self.resolution_label.setText(resolution)
    
    def reset_zoom_value(self):
        """Reset zoom to 100%."""
        self.zoom_spinbox.setValue(100)
    
    @property
    def current_zoom_percent(self) -> int:
        """Get the current zoom percentage."""
        return self.zoom_spinbox.value()


class RightPanelWidget(QSplitter):
    """Right panel containing video display, controls, and timeline."""
    
    def __init__(self,
                 on_open_file: Callable,
                 on_save_snapshot: Callable,
                 on_reset_zoom: Callable,
                 on_zoom_changed: Callable[[int], None],
                 on_frame_selected: Callable[[int], None]):
        super().__init__(Qt.Orientation.Vertical)
        
        # Create components
        self.video_canvas = VideoDisplayCanvas()
        self.control_bar = VideoControlBar(
            on_open_file, on_save_snapshot, on_reset_zoom, on_zoom_changed
        )
        self.timeline_widget = TimelineBarGraph(on_frame_selected)
        
        # Setup timeline with scroll area
        self.timeline_scroll_area = self._create_timeline_scroll_area()
        
        # Add widgets to splitter
        self.addWidget(self.video_canvas)
        self.addWidget(self.control_bar)
        self.addWidget(self.timeline_scroll_area)
        
        # Set stretch factors
        self.setStretchFactor(0, 3)  # Video canvas gets most space
        self.setStretchFactor(2, 1)  # Timeline gets some space
    
    def _create_timeline_scroll_area(self) -> QScrollArea:
        """Create and configure the timeline scroll area."""
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.timeline_widget)
        scroll_area.setWidgetResizable(False)
        scroll_area.setMinimumHeight(150)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Connect timeline to scroll area
        self.timeline_widget.set_scroll_area(scroll_area)
        
        return scroll_area


def create_main_layout(
    on_open_file: Callable,
    on_save_snapshot: Callable,
    on_reset_zoom: Callable,
    on_zoom_changed: Callable[[int], None],
    on_frame_changed: Callable[[int], None],
    on_frame_selected: Callable[[int], None]
) -> Tuple[QSplitter, PlaybackControlWidget, LeftPanelWidget, RightPanelWidget]:
    """
    Create the main application layout.
    
    Returns:
        Tuple of (main_splitter, playback_control, left_panel, right_panel)
    """
    # Create main horizontal splitter
    main_splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # Create playback control widget
    playback_control = PlaybackControlWidget(on_frame_changed)
    
    # Create left and right panels
    left_panel = LeftPanelWidget(playback_control)
    right_panel = RightPanelWidget(
        on_open_file, on_save_snapshot, on_reset_zoom, on_zoom_changed, on_frame_selected
    )
    
    # Add panels to main splitter
    main_splitter.addWidget(left_panel)
    main_splitter.addWidget(right_panel)
    
    # Set initial sizes (20% left, 80% right)
    main_splitter.setSizes([240, 960])
    
    return main_splitter, playback_control, left_panel, right_panel