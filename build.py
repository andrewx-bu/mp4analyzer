#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def build_exe():
    """Build standalone executable with PyInstaller."""
    # Clean previous builds
    for dir in ['build', 'dist']:
        if os.path.exists(dir):
            shutil.rmtree(dir)
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', 'mp4analyzer',
        '--icon', 'icon.ico' if os.path.exists('icon.ico') else 'NONE',
        '--add-data', f'src{os.pathsep}src',
        'main.py'
    ]
    
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"\n✅ Build successful! Executable at: dist/mp4anlayzer.exe")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()