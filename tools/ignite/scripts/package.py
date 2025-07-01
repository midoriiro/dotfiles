import zipfile
import tarfile
import shutil
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


def add_to_wheel(wheel_file: Path, exe_path: Path) -> None:
    """Add executable to wheel package."""
    safe_print(f"Adding to wheel: {wheel_file}")
    with zipfile.ZipFile(wheel_file, 'a') as wheel:
        wheel.write(exe_path, exe_path.name)
    safe_print("✅ Added to wheel")


def add():
    """Add executable to wheel and tar.gz packages."""
    
    exe_path = Path("dist/ignite")
    if not exe_path.exists():
        safe_print("❌ Executable not found at dist/ignite")
        return
    
    safe_print("Adding executable to packages...")
    
    # Add to wheel packages
    for wheel_file in Path("dist").glob("*.whl"):
        add_to_wheel(wheel_file, exe_path)
        
    safe_print("🎉 Done!")