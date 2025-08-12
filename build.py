#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess


def build_exe():
    """Build standalone executable with PyInstaller."""
    # Clean previous builds
    for dir in ["build", "dist"]:
        if os.path.exists(dir):
            shutil.rmtree(dir)

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--debug=imports",
        "--name",
        "mp4analyzer",
        # UI modules
        "--hidden-import",
        "ui.main_window",
        "--hidden-import",
        "ui.ui_components",
        "--hidden-import",
        "ui.video_canvas",
        "--hidden-import",
        "ui.timeline_widget",
        # src modules
        "--hidden-import",
        "src.mp4analyzer",
        "--hidden-import",
        "src.mp4analyzer.cli",
        "--hidden-import",
        "src.mp4analyzer.movieinfo",
        "--hidden-import",
        "src.mp4analyzer.parser",
        "--hidden-import",
        "src.mp4analyzer.utils",
        # src.mp4analyzer.boxes modules
        "--hidden-import",
        "src.mp4analyzer.boxes.base",
        "--hidden-import",
        "src.mp4analyzer.boxes.edts",
        "--hidden-import",
        "src.mp4analyzer.boxes.elst",
        "--hidden-import",
        "src.mp4analyzer.boxes.free",
        "--hidden-import",
        "src.mp4analyzer.boxes.ftyp",
        "--hidden-import",
        "src.mp4analyzer.boxes.iods",
        "--hidden-import",
        "src.mp4analyzer.boxes.mdat",
        "--hidden-import",
        "src.mp4analyzer.boxes.moov",
        "--hidden-import",
        "src.mp4analyzer.boxes.mvhd",
        "--hidden-import",
        "src.mp4analyzer.boxes.tkhd",
        "--hidden-import",
        "src.mp4analyzer.boxes.trak",
        # Add data folders
        "--add-data",
        f"ui{os.pathsep}ui",
        "--add-data",
        f"src{os.pathsep}src",
        "main.py",
    ]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("Build successful!")
    else:
        print("Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
