from pathlib import Path

from devcc.context import Context
from devcc.models import (ExposeFeature, Feature, RuntimeFeature,
                          WorkspaceFeature)


def test_context_initialization():
    """Test that the Context class initializes correctly."""
    context = Context()
    assert context.output is None
    assert context.dry_run is False
    assert context.features == {}


def test_context_str():
    """Test the string representation of the context."""
    context = Context()
    context.output = Path("/tmp/test.json")
    context.dry_run = True
    
    # Add some features
    context.features["runtime"] = RuntimeFeature()
    context.features["workspace"] = WorkspaceFeature()
    
    expected = "Context(output=/tmp/test.json, dry_run=True, features=['runtime', 'workspace'])"
    assert str(context) == expected


def test_context_repr():
    """Test the detailed string representation of the context."""
    context = Context()
    context.output = Path("/tmp/test.json")
    context.dry_run = True
    
    # Add some features
    runtime = RuntimeFeature()
    workspace = WorkspaceFeature()
    context.features["runtime"] = runtime
    context.features["workspace"] = workspace
    
    expected = (
        "Context("
        f"output={repr(Path('/tmp/test.json'))}, "
        "dry_run=True, "
        f"features={{'runtime': {repr(runtime)}, 'workspace': {repr(workspace)}}}"
        ")"
    )
    assert repr(context) == expected


def test_context_with_empty_features():
    """Test context string representations with no features."""
    context = Context()
    context.output = Path("/tmp/test.json")
    context.dry_run = True
    
    expected_str = "Context(output=/tmp/test.json, dry_run=True, features=[])"
    assert str(context) == expected_str
    
    expected_repr = f"Context(output={repr(Path('/tmp/test.json'))}, dry_run=True, features={{}})"
    assert repr(context) == expected_repr


def test_context_with_none_output():
    """Test context string representations with None output."""
    context = Context()
    context.dry_run = True
    context.features["expose"] = ExposeFeature()
    
    expected_str = "Context(output=None, dry_run=True, features=['expose'])"
    assert str(context) == expected_str
    
    expected_repr = "Context(output=None, dry_run=True, features={'expose': ExposeFeature(socket=None, address=None)})"
    assert repr(context) == expected_repr 