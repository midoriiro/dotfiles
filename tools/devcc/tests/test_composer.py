import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from devcc.composer import Composer
from devcc.context import Context
from devcc.models import (Env, ExposeFeature, MountPoint, MountType,
                          RuntimeFeature, WorkspaceFeature)


def test_composer_initialization():
    """Test that the Composer class initializes correctly."""
    context = Context()
    composer = Composer(context)
    assert composer.context == context
    assert composer.config == {}

def test_composer_compose_features():
    """Test that the Composer correctly composes multiple features."""
    context = Context()
    
    # Add some features
    runtime_feature = RuntimeFeature(remoteUser="dev")
    workspace_feature = WorkspaceFeature(name="test-workspace")
    expose_feature = ExposeFeature()
    
    context.features["runtime"] = runtime_feature
    context.features["workspace"] = workspace_feature
    context.features["expose"] = expose_feature
    
    composer = Composer(context)
    result = composer.compose()
    
    assert "remoteUser" in result
    assert result["remoteUser"] == "dev"
    assert "name" in result
    assert result["name"] == "test-workspace"

def test_composer_save_dry_run():
    """Test that the Composer correctly handles dry run mode."""
    context = Context()
    context.dry_run = True
    
    runtime_feature = RuntimeFeature(remoteUser="dev")
    context.features["runtime"] = runtime_feature
    
    composer = Composer(context)
    composer.compose()
    
    with patch('builtins.print') as mock_print:
        composer.save()
        mock_print.assert_called_once()
        printed_json = json.loads(mock_print.call_args[0][0])
        assert printed_json["remoteUser"] == "dev"

def test_composer_save_to_file(tmp_path):
    """Test that the Composer correctly saves to a file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        context = Context()
        context.output = Path(temp_file.name)
        
        runtime_feature = RuntimeFeature(remoteUser="dev")
        context.features["runtime"] = runtime_feature
        
        composer = Composer(context)
        composer.compose()
        composer.save()
    
        assert context.output.exists()
        with open(context.output) as f:
            saved_json = json.load(f)
            assert saved_json["remoteUser"] == "dev"

def test_composer_save_no_output_path():
    """Test that the Composer raises an error when no output path is specified."""
    context = Context()
    context.output = None
    
    composer = Composer(context)
    composer.compose()
    
    with pytest.raises(ValueError, match="No output path specified"):
        composer.save()

def test_composer_add_feature_merge_dict():
    """Test that Composer correctly merges dictionaries when adding features."""
    context = Context()
    composer = Composer(context)
    
    # First feature with a dictionary
    feature1 = RuntimeFeature(
        containerEnv=[Env(key="KEY1", value="value1")]
    )
    composer._add_feature(feature1)
    
    # Second feature with a dictionary that should merge
    feature2 = RuntimeFeature(
        containerEnv=[Env(key="KEY2", value="value2")]
    )
    composer._add_feature(feature2)
    
    assert composer.config["containerEnv"] == {
        "KEY1": "value1",
        "KEY2": "value2"
    }

def test_composer_add_feature_merge_list():
    """Test that Composer correctly merges lists when adding features."""
    context = Context()
    composer = Composer(context)
    
    # First feature with a list
    feature1 = RuntimeFeature(
        mounts=[
            MountPoint(
                source="/host/path1",
                target="/container/path1",
                type=MountType.BIND
            )
        ]
    )
    composer._add_feature(feature1)
    
    # Second feature with a list that should merge
    feature2 = RuntimeFeature(
        mounts=[
            MountPoint(
                source="/host/path2",
                target="/container/path2",
                type=MountType.BIND
            )
        ]
    )
    composer._add_feature(feature2)
    
    assert composer.config["mounts"] == [
        "source=/host/path1,target=/container/path1,type=bind",
        "source=/host/path2,target=/container/path2,type=bind"
    ]

def test_composer_add_feature_simple_value():
    """Test that Composer correctly handles simple values when adding features."""
    context = Context()
    composer = Composer(context)
    
    # First feature with a simple value
    feature1 = RuntimeFeature(remoteUser="user1")
    composer._add_feature(feature1)
    
    # Second feature with a different simple value (should override)
    feature2 = RuntimeFeature(remoteUser="user2")
    composer._add_feature(feature2)
    
    assert composer.config["remoteUser"] == "user2" 