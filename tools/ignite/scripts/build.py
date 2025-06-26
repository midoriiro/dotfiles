import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        sys.exit(1)
    
    print(f"✅ {description} completed")
    if result.stdout.strip():
        print(result.stdout)


def run():
    """Build the complete package."""
    print("🚀 Starting Ignite build process...")
    
    # Ensure we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Run this script from the project root.")
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
        
        print("\n🎉 Build completed successfully!")
            
    except KeyboardInterrupt:
        print("\n❌ Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
