import subprocess
import sys
import shutil

def build():
    # Clean
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('build', ignore_errors=True)
    
    # Build
    subprocess.run([sys.executable, '-m', 'PyInstaller', 
                   '--onefile', '--windowed', '--name', 'mp4analyzer', 'main.py'], 
                   check=True)

if __name__ == '__main__':
    build()