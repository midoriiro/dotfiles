import sys
import zipfile
from pathlib import Path

# Add the utils.py directory to the Python path
current_dir = Path(__file__).parent
utils_path = current_dir.parent.parent.parent / "scripts" / "python"
sys.path.insert(0, str(utils_path))

# Import functions from utils.py
from utils import (
    safe_print_info, 
    safe_print_error, 
    safe_print_success, 
    safe_print_done
)


def add_to_wheel(wheel_file: Path, exe_path: Path) -> None:
    """Add executable to wheel package."""
    safe_print_info(f"Adding to wheel: {wheel_file}")
    with zipfile.ZipFile(wheel_file, 'a') as wheel:
        wheel.write(exe_path, exe_path.name)
    safe_print_success("Added to wheel")


def add():
    """Add executable to wheel and tar.gz packages."""
    
    exe_path = Path("dist/ignite")
    if not exe_path.exists():
        safe_print_error("Executable not found at dist/ignite")
        return
    
    safe_print_info("Adding executable to packages...")
    
    # Add to wheel packages
    for wheel_file in Path("dist").glob("*.whl"):
        add_to_wheel(wheel_file, exe_path)
        
    safe_print_done("Done!")