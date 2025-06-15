import pytest
from typer.testing import CliRunner

from devcc.main import App
from devcc.models import ConnectionURL, MountType

runner = CliRunner()

@pytest.fixture
def app() -> App:
    app = App()
    app.register()
    return app

def test_expose_command_with_socket(app: App):
    result = runner.invoke(app.typer, ["expose", "--socket", "/tmp/host.sock:/tmp/container.sock"])
    assert result.exit_code == 0
    assert app.context.features["expose"].socket.source == "/tmp/host.sock"
    assert app.context.features["expose"].socket.target == "/tmp/container.sock"
    assert app.context.features["expose"].socket.type == MountType.BIND
    assert app.context.features["expose"].socket.options == "consistency=cached"
    assert app.context.features["expose"].address is None

def test_expose_command_with_address(app: App):
    result = runner.invoke(app.typer, ["expose", "--address", "unix:///tmp/container.sock"])
    assert result.exit_code == 0
    assert app.context.features["expose"].socket is None
    assert isinstance(app.context.features["expose"].address, ConnectionURL)
    assert str(app.context.features["expose"].address.to_string()) == "unix:///tmp/container.sock"

def test_expose_command_with_both(app: App):
    result = runner.invoke(app.typer, ["expose", "--socket", "/tmp/host.sock:/tmp/container.sock", "--address", "unix:///tmp/container.sock"])
    assert result.exit_code == 2
    assert "Both socket and address cannot be provided" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_empty_host_socket_path(app: App):
    result = runner.invoke(app.typer, ["expose", "--socket", ":/tmp/container.sock"])
    assert result.exit_code == 2
    assert "Host socket path cannot be empty" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_empty_container_socket_path(app: App):
    result = runner.invoke(app.typer, ["expose", "--socket", "/tmp/host.sock:"])
    assert result.exit_code == 2
    assert "Container socket path cannot be empty" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_empty_address(app: App):
    result = runner.invoke(app.typer, ["expose", "--address", ""])
    assert result.exit_code == 2
    assert "Address cannot be empty" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_invalid_socket_format(app: App):
    result = runner.invoke(app.typer, ["expose", "--socket", "invalid_format"])
    assert result.exit_code == 2
    assert "Socket path must be in format 'host_path:container_path'" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_relative_host_path(app: App):
    result = runner.invoke(app.typer, ["expose", "--socket", "relative/path:relative/path"])
    assert result.exit_code == 2
    assert "Host socket path must be absolute" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_relative_container_path(app: App):
    result = runner.invoke(app.typer, ["expose", "--socket", "/tmp/host.sock:relative/path"])
    assert result.exit_code == 2
    assert "Container socket path must be absolute" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_invalid_address(app: App):
    result = runner.invoke(app.typer, ["expose", "--address", "invalid://address"])
    assert result.exit_code == 2
    assert "Address must start with one of: ssh://, tcp://, unix://" in result.output
    assert app.context.features.get("expose") is None

def test_expose_command_with_feature_creation_error(app: App, monkeypatch):
    def mock_expose_feature(*args, **kwargs):
        raise Exception("Simulated feature creation error")
    
    monkeypatch.setattr("devcc.commands.expose.ExposeFeature", mock_expose_feature)
    
    result = runner.invoke(app.typer, ["expose", "--socket", "/tmp/host.sock:/tmp/container.sock"])
    assert result.exit_code == 1
    assert "Error: Simulated feature creation error" in result.output
    assert app.context.features.get("expose") is None 