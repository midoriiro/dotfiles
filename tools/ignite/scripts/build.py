import subprocess
import sys
from pathlib import Path
from .utils import safe_print, safe_subprocess_run, safe_stdout_text


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and handle errors."""
    safe_print(f"🔄 {description}...")
    safe_print(f"Running: {' '.join(cmd)}")
    
    result = safe_subprocess_run(cmd, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        error_msg = safe_stdout_text(result.stderr)
        safe_print(f"❌ Error: {error_msg}")
        sys.exit(1)
    
    safe_print(f"✅ {description} completed")
    stdout_text = safe_stdout_text(result.stdout)
    if stdout_text.strip():
        safe_print(stdout_text)


def run():
    """Build the complete package."""
    safe_print("🚀 Starting Ignite build process...")
    
    # Ensure we're in the right directory
    if not Path("pyproject.toml").exists():
        safe_print("❌ Error: pyproject.toml not found. Run this script from the project root.")
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
        
        safe_print("\n🎉 Build completed successfully!")
            
    except KeyboardInterrupt:
        safe_print("\n❌ Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        safe_print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
