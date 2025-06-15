import json
from pathlib import Path

from typer.testing import CliRunner

from devcc.context import Context
from devcc.main import App, app
from devcc.models import MountType

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


def test_app_with_all_features_and_options(app: App, runner: CliRunner):
    """Test the app with all features and options set."""
    # Example of invoking the app with all options
    result = runner.invoke(app.typer, [
        "--output", "/tmp/test.json",
        "--dry-run",
        "runtime",
        "--user", "remote:testuser",
        "--env", "container:TEST_KEY=test_value",
        "--mounts", "/host/path:/container/path:bind:ro",
        "workspace",
        "--name", "testworkspace",
        "--volume-name", "testvolume",
        "expose",
        "--address", "unix:///tmp/container.sock"
    ], catch_exceptions=False)
    assert result.exit_code == 0
    assert app.context.output == Path("/tmp/test.json")
    assert app.context.dry_run is True
    assert app.context.features["runtime"].remoteUser == "testuser"
    assert app.context.features["runtime"].containerEnv[0].key == "TEST_KEY"
    assert app.context.features["runtime"].containerEnv[0].value == "test_value"
    assert app.context.features["runtime"].mounts[0].source == "/host/path"
    assert app.context.features["runtime"].mounts[0].target == "/container/path"
    assert app.context.features["runtime"].mounts[0].type == MountType.BIND
    assert app.context.features["runtime"].mounts[0].options == "ro"
    assert app.context.features["workspace"].name == "testworkspace"
    assert app.context.features["workspace"].workspaceMount.source == "testvolume"
    assert app.context.features["workspace"].workspaceMount.target == "/workspace"
    assert app.context.features["workspace"].workspaceMount.type == MountType.VOLUME
    assert app.context.features["workspace"].workspaceMount.options == "consistency=cached"
    assert app.context.features["expose"].address.to_string() == "unix:///tmp/container.sock"
    expected_output = {
        "name": "testworkspace",
        "workspaceMount": "source=testvolume,target=/workspace,type=volume,options=consistency=cached",
        "remoteUser": "testuser",
        "containerEnv": {
            "TEST_KEY": "test_value",
            "CONTAINER_HOST": "unix:///tmp/container.sock"
        },
        "mounts": [
            "source=/host/path,target=/container/path,type=bind,options=ro"
        ]
    }
    output_dict = json.loads(result.output)
    assert output_dict == expected_output