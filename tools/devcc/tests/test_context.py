from pathlib import Path

from devcc.context import Context
from devcc.models import (ExposeFeature, Feature, RuntimeFeature,
                          WorkspaceFeature)


def test_context_initialization(context):
    """Test that the Context class initializes correctly."""
    assert context.output is None
    assert context.dry_run is False
    assert context.features == {}


def test_context_str(context_with_features):
    """Test the string representation of the context."""
    expected = "Context(output=/tmp/test.json, dry_run=True, features=['runtime', 'workspace', 'expose'])"
    assert str(context_with_features) == expected


def test_context_repr(context_with_features):
    """Test the detailed string representation of the context."""
    expected = (
        "Context("
        f"output={repr(Path('/tmp/test.json'))}, "
        "dry_run=True, "
        f"features={{'runtime': {repr(context_with_features.features['runtime'])}, "
        f"'workspace': {repr(context_with_features.features['workspace'])}, "
        f"'expose': {repr(context_with_features.features['expose'])}}}"
        ")"
    )
    assert repr(context_with_features) == expected


def test_context_with_empty_features(context):
    """Test context string representations with no features."""
    context.output = Path("/tmp/test.json")
    context.dry_run = True
    
    expected_str = "Context(output=/tmp/test.json, dry_run=True, features=[])"
    assert str(context) == expected_str
    
    expected_repr = f"Context(output={repr(Path('/tmp/test.json'))}, dry_run=True, features={{}})"
    assert repr(context) == expected_repr


def test_context_with_none_output(context, expose_feature):
    """Test context string representations with None output."""
    context.dry_run = True
    context.features["expose"] = expose_feature
    
    expected_str = "Context(output=None, dry_run=True, features=['expose'])"
    assert str(context) == expected_str
    
    expected_repr = "Context(output=None, dry_run=True, features={'expose': ExposeFeature(socket=None, address=None)})"
    assert repr(context) == expected_repr 