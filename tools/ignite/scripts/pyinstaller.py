import PyInstaller.__main__
from pathlib import Path

HERE = Path(__file__).parent.parent.absolute()
path_to_main = str(HERE / "ignite" / "main.py")

def build():
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