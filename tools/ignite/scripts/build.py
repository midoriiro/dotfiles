import subprocess
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


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and handle errors."""
    safe_print(f"🔄 {description}...")
    safe_print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        safe_print(f"❌ Error: {result.stderr}")
        sys.exit(1)
    
    safe_print(f"✅ {description} completed")
    if result.stdout.strip():
        safe_print(result.stdout)


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
