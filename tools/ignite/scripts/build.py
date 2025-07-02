import sys
from pathlib import Path

# Add the utils.py directory to the Python path
current_dir = Path(__file__).parent
utils_path = current_dir.parent.parent.parent / "scripts" / "python"
sys.path.insert(0, str(utils_path))

# Import functions from utils.py
from utils import (
    safe_print, 
    safe_subprocess_run, 
    safe_print_info, 
    safe_print_error, 
    safe_print_success, 
    safe_print_start, 
    safe_print_done
)


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and handle errors."""
    safe_print_info(f"{description}...")
    safe_print(f"Running: {' '.join(cmd)}")
    
    exit_code = safe_subprocess_run(cmd)
    
    if exit_code != 0:
        safe_print_error(f"Error: {description}")
        sys.exit(1)
    
    safe_print_success(f"{description} completed")


def run():
    """Build the complete package."""
    safe_print_start("Starting Ignite build process...")
    
    # Ensure we're in the right directory
    if not Path("pyproject.toml").exists():
        safe_print_error("pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)
    
    try:
        # Step 1: Build executable
        run_command(
            ["poetry", "run", "build-executable"],
            "Building executable with PyInstaller"
        )
        
        # Step 2: Build packages (wheel and sdist)
        run_command(
            ["poetry", "build"],
            "Building packages with Poetry"
        )
        
        # Step 3: Add executable to packages
        run_command(
            ["poetry", "run", "package-executable"],
            "Adding executable to packages"
        )
        
        safe_print_done("Build completed successfully!")
            
    except KeyboardInterrupt:
        safe_print_error("Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        safe_print_error(f"Unexpected error: {e}")
        sys.exit(1)
