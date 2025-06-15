from pathlib import Path

from typer.testing import CliRunner

from devcc.context import Context
from devcc.main import App, app

runner = CliRunner()

def test_app_initialization(app: App):
    """Test that the App class initializes correctly."""
    assert isinstance(app.context, Context)
    assert app.typer is not None

def test_app_register(app: App, runner: CliRunner):
    """Test that the app registers commands correctly."""
    # Test that the commands are registered
    result = runner.invoke(app.typer, ["--help"])
    assert result.exit_code == 0
    assert "runtime" in result.output
    assert "workspace" in result.output
    assert "expose" in result.output

def test_app_context_initialization(app: App, runner: CliRunner):
    """Test that the context is initialized correctly with options."""
    # Test with output path
    output_path = Path("/tmp/test.json")
    result = runner.invoke(app.typer, ["--output", str(output_path)])
    assert result.exit_code == 0
    assert app.context.output == output_path
    
    # Test with dry run
    result = runner.invoke(app.typer, ["--dry-run"])
    assert result.exit_code == 0
    assert app.context.dry_run is True

def test_app_context_finalization(app: App, runner: CliRunner):
    """Test that the context is finalized correctly."""
    # Run a simple command to trigger finalization
    result = runner.invoke(app.typer, ["--dry-run", "runtime"])
    assert result.exit_code == 0
    
    # Check that finalization message is printed
    assert "{}" in result.output

def test_app_properties(app: App):
    """Test that the app properties work correctly."""
    # Test context property
    assert isinstance(app.context, Context)
    
    # Test typer property
    assert app.typer is not None

def test_module_level_app():
    """Test that the module-level app instance works correctly."""
    assert isinstance(app, App)
    assert app.typer is not None
    
    # Test that the module-level app has commands registered
    result = runner.invoke(app.typer, ["--help"])
    assert result.exit_code == 0
    assert "runtime" in result.output
    assert "workspace" in result.output
    assert "expose" in result.output

def test_main_module_execution():
    """Test that the main module can be executed directly."""
    import subprocess
    import sys
    from pathlib import Path

    # Get the path to main.py
    main_path = Path(__file__).parent.parent / "devcc" / "main.py"
    
    # Run the module directly
    result = subprocess.run([sys.executable, str(main_path), "--help"], 
                          capture_output=True, 
                          text=True)
    
    assert result.returncode == 0
    assert "Usage:" in result.stdout 