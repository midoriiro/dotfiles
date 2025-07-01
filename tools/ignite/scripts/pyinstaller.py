import PyInstaller.__main__
import sys
import os
from pathlib import Path

# Force UTF-8 encoding for Windows compatibility
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    # Reconfigure stdout and stderr to use UTF-8
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def safe_print(text: str) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII if emoji encoding fails
        fallback_map = {
            "🔄": "[INFO]",
            "❌": "[ERROR]",
            "✅": "[SUCCESS]",
            "🚀": "[START]",
            "🎉": "[SUCCESS]"
        }
        for emoji, replacement in fallback_map.items():
            text = text.replace(emoji, replacement)
        print(text)


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