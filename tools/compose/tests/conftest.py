import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from compose.context import Context
from compose.main import App
from compose.models import (ConnectionURL, ExposeFeature, Feature,
                            RuntimeFeature, WorkspaceFeature)


@pytest.fixture
def context():
    """Fixture providing a basic Context instance."""
    return Context()

@pytest.fixture
def context_with_features():
    """Fixture providing a Context instance with all features."""
    context = Context()
    context.output = Path("/tmp/test.json")
    context.dry_run = True
    
    # Add all features
    context.features["runtime"] = RuntimeFeature()
    context.features["workspace"] = WorkspaceFeature()
    context.features["expose"] = ExposeFeature()
    
    return context

@pytest.fixture
def runtime_feature():
    """Fixture providing a RuntimeFeature instance."""
    return RuntimeFeature()

@pytest.fixture
def workspace_feature():
    """Fixture providing a WorkspaceFeature instance."""
    return WorkspaceFeature()

@pytest.fixture
def expose_feature():
    """Fixture providing an ExposeFeature instance."""
    return ExposeFeature()

@pytest.fixture
def ssh_connection_url():
    """Fixture providing a valid SSH connection URL."""
    return ConnectionURL.from_string("ssh://hostname:22")

@pytest.fixture
def tcp_connection_url():
    """Fixture providing a valid TCP connection URL."""
    return ConnectionURL.from_string("tcp://localhost:8080")

@pytest.fixture
def unix_connection_url():
    """Fixture providing a valid Unix socket connection URL."""
    return ConnectionURL.from_string("unix:///tmp/socket.sock")

@pytest.fixture
def app():
    """Fixture providing a configured App instance with a temporary output file."""
    app = App()
    app.register()
    return app

@pytest.fixture
def runner():
    """Fixture providing a CliRunner instance."""
    return CliRunner()

@pytest.fixture
def runner_args():
    """Fixture providing arguments for the CliRunner invoke method."""
    return {
        "catch_exceptions": False
    }
