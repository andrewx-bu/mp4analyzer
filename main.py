# Entry point for MP4 Analyzer application.
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MP4AnalyzerMainWindow


def main():
    """Main entry point for the MP4 Analyzer application."""
    # Create application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Create and show main window
    main_window = MP4AnalyzerMainWindow()
    main_window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
