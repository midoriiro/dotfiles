import json
import logging
from pathlib import Path
from typing import Dict, Any
from collections import OrderedDict

import pytest
from assertpy import assert_that

from ignite.composers import ContainerComposer
from ignite.models.container import (
    Container, 
    Workspace as ContainerWorkspace,
    Runtime, 
    Expose, 
    Build, 
    Image, 
    Network, 
    Extensions,
    Env,
    EnvType,
    Users,
    Mount,
    MountType,
    Socket,
    URL,
    URLScheme
)
from ignite.models.policies import FolderCreatePolicy, FileWritePolicy
from ignite.logging import FilesystemMessage


class TestContainerComposerInitialization:
    """Test ContainerComposer initialization and basic properties."""

    def test_container_composer_initialization(self, minimal_container_configuration):
        """Test that ContainerComposer initializes correctly with a container."""
        composer = ContainerComposer(minimal_container_configuration)
        
        assert_that(composer).is_not_none()
        assert_that(composer._ContainerComposer__container).is_equal_to(minimal_container_configuration)
        assert_that(composer._ContainerComposer__config).is_none()

    def test_feature_order_is_correct(self, minimal_container_configuration):
        """Test that the feature order is correctly defined."""
        composer = ContainerComposer(minimal_container_configuration)
        expected_order = [
            ContainerWorkspace.feature_name(),
            Runtime.feature_name(),
            Expose.feature_name(),
            Build.feature_name(),
            Image.feature_name(),
            Network.feature_name(),
            Extensions.feature_name()
        ]
        
        assert_that(composer._ContainerComposer__feature_order).is_equal_to(expected_order)

    def test_inherits_from_composer(self, minimal_container_configuration):
        """Test that ContainerComposer inherits from Composer base class."""
        composer = ContainerComposer(minimal_container_configuration)
        
        assert_that(composer).is_instance_of(ContainerComposer)
        assert_that(hasattr(composer, 'logger')).is_true()
        assert_that(hasattr(composer, 'compose')).is_true()
        assert_that(hasattr(composer, 'save')).is_true()


class TestContainerComposerCompose:
    """Test ContainerComposer compose functionality."""

    def test_compose_with_minimal_container(self, minimal_container_configuration):
        """Test composing a minimal container configuration."""
        composer = ContainerComposer(minimal_container_configuration)
        composer.compose()
        
        assert_that(composer._ContainerComposer__config).is_not_none()
        expected_config = {
            'name': minimal_container_configuration.workspace.name,
            'workspaceMount': f"source={minimal_container_configuration.workspace.volume_name},target={minimal_container_configuration.workspace.folder},type=volume",
            'workspaceFolder': minimal_container_configuration.workspace.folder,
            'image': minimal_container_configuration.image.name
        }
        assert_that(composer._ContainerComposer__config).is_equal_to(expected_config)

    def test_compose_with_all_features(self):
        """Test composing a container with all features."""
        container = Container(
            workspace=ContainerWorkspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-volume"
            ),
            runtime=Runtime(
                user=Users(remote="host-user", container="dev-user"),
                env=[Env(key="DEBUG", value="true", type=EnvType.CONTAINER)]
            ),
            expose=Expose(
                socket=Socket(host="/var/run/docker.sock", container="/var/run/docker.sock")
            ),
            image=Image(name="test-image", tag="latest"),
            network=Network(name="test-network"),
            extensions=Extensions(vscode=["ms-python.python"])
        )
        
        composer = ContainerComposer(container)
        composer.compose()
        
        config = composer._ContainerComposer__config
        assert_that(config).is_not_none()
        assert_that(config).contains_key('name')
        assert_that(config).contains_key('workspaceMount')
        assert_that(config).contains_key('workspaceFolder')
        assert_that(config).contains_key('remoteUser')
        assert_that(config).contains_key('containerUser')
        assert_that(config).contains_key('containerEnv')
        assert_that(config).contains_key('mounts')
        assert_that(config).contains_key('image')
        assert_that(config).contains_key('runArgs')
        assert_that(config).contains_key('customizations')

    def test_compose_with_build_instead_of_image(self):
        """Test composing a container with build configuration instead of image."""
        container = Container(
            workspace=ContainerWorkspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-volume"
            ),
            build=Build(container_file="Dockerfile")
        )
        
        composer = ContainerComposer(container)
        composer.compose()
        
        config = composer._ContainerComposer__config
        assert_that(config).is_not_none()
        assert_that(config).contains_key('build')
        assert_that(config).does_not_contain_key('image')

    def test_compose_preserves_feature_order(self):
        """Test that compose preserves the defined feature order."""
        container = Container(
            workspace=ContainerWorkspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-volume"
            ),
            runtime=Runtime(user="test-user"),
            image=Image(name="test-image")
        )
        
        composer = ContainerComposer(container)
        composer.compose()
        
        # The config should be an OrderedDict preserving the feature order
        config = composer._ContainerComposer__config
        assert_that(config).is_instance_of(OrderedDict)
        
        # Check that workspace comes before runtime and image
        config_keys = list(config.keys())
        workspace_index = config_keys.index('workspaceMount')
        runtime_index = config_keys.index('remoteUser')
        
        assert_that(workspace_index).is_less_than(runtime_index)


class TestContainerComposerAddFeature:
    """Test ContainerComposer _add_feature method."""

    def test_add_feature_with_new_key(self, minimal_container_configuration):
        """Test adding a feature with a new key."""
        composer = ContainerComposer(minimal_container_configuration)
        features = {}
        feature = {'newKey': 'newValue'}
        
        composer._add_feature(features, feature)
        
        assert_that(features).contains_key('newKey')
        assert_that(features['newKey']).is_equal_to('newValue')

    def test_add_feature_merges_dict_values(self, minimal_container_configuration):
        """Test that _add_feature merges dictionary values correctly."""
        composer = ContainerComposer(minimal_container_configuration)
        features = {'existingKey': {'existing': 'value'}}
        feature = {'existingKey': {'new': 'value'}}
        
        composer._add_feature(features, feature)
        
        assert_that(features['existingKey']).contains_key('existing')
        assert_that(features['existingKey']).contains_key('new')
        assert_that(features['existingKey']['existing']).is_equal_to('value')
        assert_that(features['existingKey']['new']).is_equal_to('value')

    def test_add_feature_extends_list_values(self, minimal_container_configuration):
        """Test that _add_feature extends list values correctly."""
        composer = ContainerComposer(minimal_container_configuration)
        features = {'existingKey': ['existing', 'value']}
        feature = {'existingKey': ['new', 'value']}
        
        composer._add_feature(features, feature)
        
        assert_that(features['existingKey']).contains('existing')
        assert_that(features['existingKey']).contains('new')
        assert_that(features['existingKey']).is_length(4)

    def test_add_feature_overwrites_non_dict_non_list(self, minimal_container_configuration):
        """Test that _add_feature overwrites non-dict, non-list values."""
        composer = ContainerComposer(minimal_container_configuration)
        features = {'existingKey': 'oldValue'}
        feature = {'existingKey': 'newValue'}
        
        composer._add_feature(features, feature)
        
        assert_that(features['existingKey']).is_equal_to('newValue')


class TestContainerComposerSave:
    """Test ContainerComposer save functionality."""

    def test_save_without_compose_raises_error(self, minimal_container_configuration, tmp_path):
        """Test that save raises error when compose hasn't been called."""
        composer = ContainerComposer(minimal_container_configuration)
        
        with pytest.raises(ValueError, match="Configuration is not composed yet."):
            composer.save(tmp_path)

    def test_save_creates_devcontainer_directory(self, minimal_container_configuration, tmp_path):
        """Test that save creates the .devcontainer directory."""
        composer = ContainerComposer(minimal_container_configuration)
        composer.compose()
        
        composer.save(tmp_path)

        json_path = Path(tmp_path, ".devcontainer", "devcontainer.json")
        assert_that(str(json_path)).exists()
        assert_that(str(json_path)).is_file()
        

    def test_save_writes_valid_json(self, minimal_container_configuration, tmp_path):
        """Test that save writes valid JSON content."""
        composer = ContainerComposer(minimal_container_configuration)
        composer.compose()
        
        composer.save(tmp_path)
        
        json_path = Path(tmp_path, ".devcontainer", "devcontainer.json")
        content = json_path.read_text()
        
        # Should be valid JSON
        parsed_json = json.loads(content)
        assert_that(parsed_json).is_instance_of(dict)

    def test_save_writes_correct_configuration(self, minimal_container_configuration, tmp_path):
        """Test that save writes the correct configuration content."""
        composer = ContainerComposer(minimal_container_configuration)
        composer.compose()
        
        composer.save(tmp_path)
        
        json_path = Path(tmp_path, ".devcontainer", "devcontainer.json")
        content = json.loads(json_path.read_text())
        
        expected_config = {
            'name': minimal_container_configuration.workspace.name,
            'workspaceMount': f"source={minimal_container_configuration.workspace.volume_name},target={minimal_container_configuration.workspace.folder},type=volume",
            'workspaceFolder': minimal_container_configuration.workspace.folder,
            'image': minimal_container_configuration.image.name
        }
        assert_that(content).is_equal_to(expected_config)

    def test_save_uses_correct_policies(self, minimal_container_configuration, tmp_path, caplog):
        """Test that save uses the correct folder and file policies."""
        composer = ContainerComposer(minimal_container_configuration)
        composer.compose()
        
        composer.save(tmp_path)
        
        # Check that the correct policies are used (ALWAYS for folder, OVERWRITE for file)
        devcontainer_path = Path(tmp_path, ".devcontainer")
        assert_that(str(devcontainer_path)).exists()
        
        # Verify logging messages indicate the correct policies were used
        log_records = [record.message for record in caplog.records]
        assert_that(log_records[0]).is_equal_to(f"Folder '{devcontainer_path}' created.")
        assert_that(log_records[1]).is_equal_to(f"File '{devcontainer_path}/devcontainer.json' saved.")

