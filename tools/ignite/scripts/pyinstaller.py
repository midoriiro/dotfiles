import PyInstaller.__main__
from pathlib import Path
from .utils import safe_print


HERE = Path(__file__).parent.parent.absolute()
path_to_main = str(HERE / "ignite" / "main.py")

def build():
    safe_print("🚀 Building executable with PyInstaller...")
    PyInstaller.__main__.run([
        path_to_main,
        '--onefile',
        '--name', 'ignite',
        '--specpath', 'build',          
        '--distpath', 'dist',
        '--workpath', 'build/temp',
        '--collect-submodules', 'ignite',
        '--strip',
        '--clean',
    ])
    safe_print("✅ Executable built successfully!")