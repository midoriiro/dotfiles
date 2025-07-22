import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.container import (
    URL,
    Build,
    Container,
    Env,
    Expose,
    Extensions,
    Image,
    Mount,
    MountType,
    Network,
    Runtime,
    Socket,
    URLScheme,
    Users,
    Workspace,
)


class TestValidContainer:
    """Test cases for valid container configurations."""

    def test_minimal_container_with_image(self):
        """Test that a minimal container with image is accepted."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
        )
        assert_that(container.workspace.name).is_equal_to("test-workspace")
        assert_that(container.image.name).is_equal_to("test-image")
        assert_that(container.runtime).is_none()
        assert_that(container.expose).is_none()
        assert_that(container.build).is_none()
        assert_that(container.network).is_none()
        assert_that(container.extensions).is_none()

    def test_minimal_container_with_build(self):
        """Test that a minimal container with build is accepted."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            build=Build(container_file="Containerfile"),
        )
        assert_that(container.workspace.name).is_equal_to("test-workspace")
        assert_that(container.build.container_file).is_equal_to("Containerfile")
        assert_that(container.image).is_none()

    def test_container_with_all_optional_fields(self):
        """Test that a container with all optional fields is accepted."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            runtime=Runtime(
                user=Users(remote="remote-user", container="container-user"),
                env=[Env(key="TEST_VAR", value="test_value")],
                mounts=[
                    Mount(
                        source="/host/path",
                        target="/container/path",
                        type=MountType.BIND,
                    )
                ],
            ),
            expose=Expose(
                socket=Socket(host="/host/socket", container="/container/socket")
            ),
            network=Network(name="test-network"),
            extensions=Extensions(vscode=["ms-python.python"]),
        )
        assert_that(container.workspace.name).is_equal_to("test-workspace")
        assert_that(container.image.name).is_equal_to("test-image")
        assert_that(container.runtime).is_not_none()
        assert_that(container.expose).is_not_none()
        assert_that(container.network).is_not_none()
        assert_that(container.extensions).is_not_none()


class TestContainerValidation:
    """Test cases for Container validation."""

    def test_container_without_workspace_raises_error(self):
        """Test that container without workspace raises validation error."""
        with pytest.raises(ValidationError, match="Field required"):
            Container(image=Image(name="test-image"))

    def test_container_without_image_and_build_raises_error(self):
        """Test that container without both image and build raises validation error."""
        with pytest.raises(
            ValueError, match="At least one of 'image' or 'build' must be set"
        ):
            Container(
                workspace=Workspace(
                    name="test-workspace",
                    folder="/workspace",
                    volume_name="test-workspace-volume",
                )
            )

    def test_container_with_both_image_and_build_raises_error(self):
        """Test that container with both image and build raises validation error."""
        with pytest.raises(
            ValueError, match="Only one of 'image' or 'build' can be set"
        ):
            Container(
                workspace=Workspace(
                    name="test-workspace",
                    folder="/workspace",
                    volume_name="test-workspace-volume",
                ),
                image=Image(name="test-image"),
                build=Build(container_file="Containerfile"),
            )


class TestContainerComposeMethod:
    """Test cases for the compose method of Container."""

    def test_compose_minimal_with_image(self):
        """Test that compose method works correctly with minimal image configuration."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
        )
        result = container.compose()

        expected = {
            "workspace": {
                "name": "test-workspace",
                "workspaceFolder": "/workspace",
                "workspaceMount": "source=test-workspace-volume,target=/workspace,type=volume",
            },
            "image": {"image": "test-image"},
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_minimal_with_build(self):
        """Test that compose method works correctly with minimal build configuration."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            build=Build(container_file="Containerfile"),
        )
        result = container.compose()

        expected = {
            "workspace": {
                "name": "test-workspace",
                "workspaceFolder": "/workspace",
                "workspaceMount": "source=test-workspace-volume,target=/workspace,type=volume",
            },
            "build": {"build": {"dockerFile": "Containerfile"}},
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_with_runtime(self):
        """Test that compose method works correctly with runtime configuration."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            runtime=Runtime(
                user=Users(remote="remote-user", container="container-user"),
                env=[Env(key="TEST_VAR", value="test_value")],
                mounts=[
                    Mount(
                        source="/host/path",
                        target="/container/path",
                        type=MountType.BIND,
                    )
                ],
            ),
        )
        result = container.compose()

        # Check that runtime is included
        assert_that(result).contains_key("runtime")
        runtime_data = result["runtime"]
        assert_that(runtime_data).contains_key("remoteUser")
        assert_that(runtime_data).contains_key("containerUser")
        assert_that(runtime_data).contains_key("remoteEnv")
        assert_that(runtime_data).contains_key("mounts")

    def test_compose_with_expose(self):
        """Test that compose method works correctly with expose configuration."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            expose=Expose(
                socket=Socket(host="/host/socket", container="/container/socket")
            ),
        )
        result = container.compose()

        # Check that expose is included
        assert_that(result).contains_key("expose")
        expose_data = result["expose"]
        assert_that(expose_data).contains_key("mounts")
        assert_that(expose_data["mounts"]).is_length(1)
        assert_that(expose_data["mounts"][0]).is_equal_to(
            "source=/host/socket,target=/container/socket,type=bind"
        )

    def test_compose_with_network(self):
        """Test that compose method works correctly with network configuration."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            network=Network(name="test-network"),
        )
        result = container.compose()

        # Check that network is included
        assert_that(result).contains_key("network")
        network_data = result["network"]
        assert_that(network_data).contains_key("runArgs")
        assert_that(network_data["runArgs"]).is_length(1)
        assert_that(network_data["runArgs"][0]).is_equal_to("--network=test-network")

    def test_compose_with_extensions(self):
        """Test that compose method works correctly with extensions configuration."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            extensions=Extensions(vscode=["ms-python.python"]),
        )
        result = container.compose()

        # Check that extensions is included
        assert_that(result).contains_key("extensions")
        extensions_data = result["extensions"]
        assert_that(extensions_data).contains_key("customizations")
        assert_that(extensions_data["customizations"]).contains_key("vscode")
        assert_that(extensions_data["customizations"]["vscode"]).contains_key(
            "extensions"
        )
        assert_that(
            extensions_data["customizations"]["vscode"]["extensions"]
        ).is_length(1)
        assert_that(
            extensions_data["customizations"]["vscode"]["extensions"][0]
        ).is_equal_to("ms-python.python")

    def test_compose_with_all_fields(self):
        """Test that compose method works correctly with all fields."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            runtime=Runtime(
                user=Users(remote="remote-user", container="container-user")
            ),
            expose=Expose(
                socket=Socket(host="/host/socket", container="/container/socket")
            ),
            network=Network(name="test-network"),
            extensions=Extensions(vscode=["ms-python.python"]),
        )
        result = container.compose()

        # Check that all expected keys are present
        expected_keys = [
            "workspace",
            "image",
            "runtime",
            "expose",
            "network",
            "extensions",
        ]
        for key in expected_keys:
            assert_that(result).contains_key(key)

    def test_compose_structure(self):
        """Test that compose method returns the correct structure."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
        )
        result = container.compose()

        # Check that the structure is correct
        assert_that(result).is_instance_of(dict)
        assert_that(result).contains_key("workspace")
        assert_that(result).contains_key("image")


class TestContainerFeatureName:
    """Test cases for the feature_name method of Container."""

    def test_feature_name(self):
        """Test that feature_name returns the correct name."""
        assert_that(Container.feature_name()).is_equal_to("container")


class TestContainerInheritance:
    """Test cases for Container inheritance from Feature."""

    def test_container_inherits_from_feature(self):
        """Test that Container inherits from Feature."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
        )
        assert_that(container).is_instance_of(Container)
        # Check that it has the compose method
        assert_that(hasattr(container, "compose")).is_true()
        # Check that it has the feature_name class method
        assert_that(hasattr(Container, "feature_name")).is_true()

    def test_container_compose_returns_dict(self):
        """Test that Container.compose() returns a dictionary."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
        )
        result = container.compose()
        assert_that(result).is_instance_of(dict)

    def test_container_feature_name_returns_string(self):
        """Test that Container.feature_name() returns a string."""
        result = Container.feature_name()
        assert_that(result).is_instance_of(str)


class TestContainerEdgeCases:
    """Test cases for edge cases in Container validation."""

    def test_container_with_none_optional_fields(self):
        """Test that container with None optional fields is valid."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            runtime=None,
            expose=None,
            build=None,
            network=None,
            extensions=None,
        )
        assert_that(container.runtime).is_none()
        assert_that(container.expose).is_none()
        assert_that(container.build).is_none()
        assert_that(container.network).is_none()
        assert_that(container.extensions).is_none()

    def test_container_with_complex_runtime_configuration(self):
        """Test that container with complex runtime configuration is valid."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            runtime=Runtime(
                user=Users(remote="remote-user", container="container-user"),
                env=[
                    Env(key="ENV1", value="value1", type="remote"),
                    Env(key="ENV2", value="value2", type="container"),
                ],
                mounts=[
                    Mount(
                        source="/host/path1",
                        target="/container/path1",
                        type=MountType.BIND,
                        options=["ro"],
                    ),
                    Mount(
                        source="volume1",
                        target="/container/path2",
                        type=MountType.VOLUME,
                    ),
                ],
            ),
        )
        result = container.compose()
        assert_that(result).contains_key("runtime")
        runtime_data = result["runtime"]
        assert_that(runtime_data).contains_key("remoteUser")
        assert_that(runtime_data).contains_key("containerUser")
        assert_that(runtime_data).contains_key("remoteEnv")
        assert_that(runtime_data).contains_key("containerEnv")
        assert_that(runtime_data).contains_key("mounts")

    def test_container_with_url_expose(self):
        """Test that container with URL expose configuration is valid."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            image=Image(name="test-image"),
            expose=Expose(address=URL(scheme=URLScheme.SSH, host="localhost", port=22)),
        )
        result = container.compose()
        assert_that(result).contains_key("expose")
        expose_data = result["expose"]
        assert_that(expose_data).contains_key("remoteEnv")
        assert_that(expose_data["remoteEnv"]).contains_key("CONTAINER_HOST")

    def test_container_with_build_context_and_target(self):
        """Test that container with build context and target is valid."""
        container = Container(
            workspace=Workspace(
                name="test-workspace",
                folder="/workspace",
                volume_name="test-workspace-volume",
            ),
            build=Build(
                container_file="Containerfile",
                context="build-context",
                target="build-stage",
            ),
        )
        result = container.compose()
        assert_that(result).contains_key("build")
        build_data = result["build"]
        assert_that(build_data).contains_key("build")
        assert_that(build_data["build"]).contains_key("dockerFile")
        assert_that(build_data["build"]).contains_key("context")
        assert_that(build_data["build"]).contains_key("target")
