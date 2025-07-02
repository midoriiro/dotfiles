import sys
import PyInstaller.__main__
from pathlib import Path

# Add the utils.py directory to the Python path
current_dir = Path(__file__).parent
utils_path = current_dir.parent.parent.parent / "scripts" / "python"
sys.path.insert(0, str(utils_path))

# Import functions from utils.py
from utils import ( 
    safe_print_start, 
    safe_print_success
)


HERE = Path(__file__).parent.parent.absolute()
path_to_main = str(HERE / "ignite" / "main.py")

def build():
    safe_print_start("Building executable with PyInstaller...")
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
    safe_print_success("Executable built successfully!")