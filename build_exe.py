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
        "--name",
        "mp4analyzer",
        "--paths",
        ".",
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
