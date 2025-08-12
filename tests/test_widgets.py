import pytest

pytest.importorskip("PyQt6.QtCore")

from PyQt6.QtCore import Qt
from ui.main_window import MP4AnalyzerMainWindow
from ui.ui_components import PlaybackControlWidget


def test_main_window_initialization(qtbot):
    """Ensure the main window sets up its title and key widgets."""
    window = MP4AnalyzerMainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "MP4 Analyzer"
    assert isinstance(window._playback_control, PlaybackControlWidget)
    assert window._playback_control in window._left_panel.findChildren(
        PlaybackControlWidget
    )
    assert window._right_panel.video_canvas is not None


def test_playback_control_widget(qtbot):
    """Verify playback control has essential child widgets."""
    widget = PlaybackControlWidget(lambda index: None)
    qtbot.addWidget(widget)

    assert widget.frame_slider.orientation() == Qt.Orientation.Horizontal
    assert widget.previous_button.text() == "<"
    assert widget.next_button.text() == ">"


def test_playback_control_behavior(qtbot):
    calls = []
    w = PlaybackControlWidget(lambda i: calls.append(i))
    qtbot.addWidget(w)

    w.set_frame_range(10)
    assert w.frame_slider.minimum() == 0
    assert w.frame_slider.maximum() == 9
    assert w.frame_slider.value() == 0

    w.set_current_frame(3, 10)
    assert w.frame_counter_label.text() == "4 / 10"
    assert w.frame_slider.value() == 3

    # Changing slider should invoke callback
    w.frame_slider.setValue(5)
    assert calls[-1] == 5
