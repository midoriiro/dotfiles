import zipfile
import tarfile
import shutil
from pathlib import Path
from .utils import safe_print


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