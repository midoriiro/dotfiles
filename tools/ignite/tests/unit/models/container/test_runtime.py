import pytest
from assertpy import assert_that

from ignite.models.container import Env, EnvType, Mount, MountType, Runtime, Users


class TestValidRuntime:
    """Test cases for valid runtime configurations."""

    def test_runtime_with_no_parameters(self):
        """Test that runtime with no parameters is accepted."""
        runtime = Runtime()
        assert_that(runtime.user).is_none()
        assert_that(runtime.env).is_none()
        assert_that(runtime.mounts).is_none()

    def test_runtime_with_single_user(self):
        """Test that runtime with single user identifier is accepted."""
        runtime = Runtime(user="developer")
        assert_that(runtime.user).is_equal_to("developer")
        assert_that(runtime.env).is_none()
        assert_that(runtime.mounts).is_none()

    def test_runtime_with_users_object(self):
        """Test that runtime with Users object is accepted."""
        users = Users(remote="developer", container="appuser")
        runtime = Runtime(user=users)
        assert_that(runtime.user).is_equal_to(users)
        assert_that(runtime.env).is_none()
        assert_that(runtime.mounts).is_none()

    def test_runtime_with_single_env(self):
        """Test that runtime with single environment variable is accepted."""
        env = Env(key="DATABASE_URL", value="postgresql://localhost:5432/mydb")
        runtime = Runtime(env=[env])
        assert_that(runtime.user).is_none()
        assert_that(runtime.env).is_equal_to([env])
        assert_that(runtime.mounts).is_none()

    def test_runtime_with_multiple_env(self):
        """Test that runtime with multiple environment variables is accepted."""
        env1 = Env(key="DATABASE_URL", value="postgresql://localhost:5432/mydb")
        env2 = Env(key="DEBUG", value="true")
        runtime = Runtime(env=[env1, env2])
        assert_that(runtime.user).is_none()
        assert_that(runtime.env).is_equal_to([env1, env2])
        assert_that(runtime.mounts).is_none()

    def test_runtime_with_single_mount(self):
        """Test that runtime with single mount is accepted."""
        mount = Mount(
            source="/home/user/data", target="/workspace/data", type=MountType.BIND
        )
        runtime = Runtime(mounts=[mount])
        assert_that(runtime.user).is_none()
        assert_that(runtime.env).is_none()
        assert_that(runtime.mounts).is_equal_to([mount])

    def test_runtime_with_multiple_mounts(self):
        """Test that runtime with multiple mounts is accepted."""
        mount1 = Mount(
            source="/home/user/data", target="/workspace/data", type=MountType.BIND
        )
        mount2 = Mount(source="cache-volume", target="/cache", type=MountType.VOLUME)
        runtime = Runtime(mounts=[mount1, mount2])
        assert_that(runtime.user).is_none()
        assert_that(runtime.env).is_none()
        assert_that(runtime.mounts).is_equal_to([mount1, mount2])

    def test_runtime_with_all_parameters(self):
        """Test that runtime with all parameters is accepted."""
        users = Users(remote="developer", container="appuser")
        env = Env(key="DATABASE_URL", value="postgresql://localhost:5432/mydb")
        mount = Mount(
            source="/home/user/data", target="/workspace/data", type=MountType.BIND
        )
        runtime = Runtime(user=users, env=[env], mounts=[mount])
        assert_that(runtime.user).is_equal_to(users)
        assert_that(runtime.env).is_equal_to([env])
        assert_that(runtime.mounts).is_equal_to([mount])


class TestRuntimeCompose:
    """Test cases for runtime composition."""

    def test_compose_empty_runtime(self):
        """Test that empty runtime composes to empty dictionary."""
        runtime = Runtime()
        result = runtime.compose()
        assert_that(result).is_equal_to({})

    def test_compose_runtime_with_single_user(self):
        """Test that runtime with single user composes correctly."""
        runtime = Runtime(user="developer")
        result = runtime.compose()
        expected = {"remoteUser": "developer", "containerUser": "developer"}
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_users_object(self):
        """Test that runtime with Users object composes correctly."""
        users = Users(remote="developer", container="appuser")
        runtime = Runtime(user=users)
        result = runtime.compose()
        expected = {"remoteUser": "developer", "containerUser": "appuser"}
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_single_remote_env(self):
        """
        Test that runtime with single remote environment variable composes correctly.
        """
        env = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.REMOTE,
        )
        runtime = Runtime(env=[env])
        result = runtime.compose()
        expected = {"remoteEnv": {"DATABASE_URL": "postgresql://localhost:5432/mydb"}}
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_single_container_env(self):
        """
        Test that runtime with single container environment variable composes correctly.
        """
        env = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.CONTAINER,
        )
        runtime = Runtime(env=[env])
        result = runtime.compose()
        expected = {
            "containerEnv": {"DATABASE_URL": "postgresql://localhost:5432/mydb"}
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_multiple_env_same_type(self):
        """
        Test that runtime with multiple environment variables of same type composes
        correctly.
        """
        env1 = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.REMOTE,
        )
        env2 = Env(key="DEBUG", value="true", type=EnvType.REMOTE)
        runtime = Runtime(env=[env1, env2])
        result = runtime.compose()
        expected = {
            "remoteEnv": {
                "DATABASE_URL": "postgresql://localhost:5432/mydb",
                "DEBUG": "true",
            }
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_multiple_env_different_types(self):
        """
        Test that runtime with multiple environment variables of different types
        composes correctly.
        """
        env1 = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.REMOTE,
        )
        env2 = Env(key="DEBUG", value="true", type=EnvType.CONTAINER)
        runtime = Runtime(env=[env1, env2])
        result = runtime.compose()
        expected = {
            "remoteEnv": {"DATABASE_URL": "postgresql://localhost:5432/mydb"},
            "containerEnv": {"DEBUG": "true"},
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_single_mount(self):
        """Test that runtime with single mount composes correctly."""
        mount = Mount(
            source="/home/user/data", target="/workspace/data", type=MountType.BIND
        )
        runtime = Runtime(mounts=[mount])
        result = runtime.compose()
        expected = {
            "mounts": ["source=/home/user/data,target=/workspace/data,type=bind"]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_mount_with_options(self):
        """Test that runtime with mount with options composes correctly."""
        mount = Mount(
            source="/home/user/data",
            target="/workspace/data",
            type=MountType.BIND,
            options=["ro", "noexec"],
        )
        runtime = Runtime(mounts=[mount])
        result = runtime.compose()
        expected = {
            "mounts": [
                "source=/home/user/data,target=/workspace/data,type=bind,options=ro,"
                "noexec"
            ]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_multiple_mounts(self):
        """Test that runtime with multiple mounts composes correctly."""
        mount1 = Mount(
            source="/home/user/data", target="/workspace/data", type=MountType.BIND
        )
        mount2 = Mount(source="cache-volume", target="/cache", type=MountType.VOLUME)
        runtime = Runtime(mounts=[mount1, mount2])
        result = runtime.compose()
        expected = {
            "mounts": [
                "source=/home/user/data,target=/workspace/data,type=bind",
                "source=cache-volume,target=/cache,type=volume",
            ]
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_runtime_with_all_components(self):
        """Test that runtime with all components composes correctly."""
        users = Users(remote="developer", container="appuser")
        env1 = Env(
            key="DATABASE_URL",
            value="postgresql://localhost:5432/mydb",
            type=EnvType.REMOTE,
        )
        env2 = Env(key="DEBUG", value="true", type=EnvType.CONTAINER)
        mount = Mount(
            source="/home/user/data", target="/workspace/data", type=MountType.BIND
        )
        runtime = Runtime(user=users, env=[env1, env2], mounts=[mount])
        result = runtime.compose()
        expected = {
            "remoteUser": "developer",
            "containerUser": "appuser",
            "remoteEnv": {"DATABASE_URL": "postgresql://localhost:5432/mydb"},
            "containerEnv": {"DEBUG": "true"},
            "mounts": ["source=/home/user/data,target=/workspace/data,type=bind"],
        }
        assert_that(result).is_equal_to(expected)


class TestRuntimeEdgeCases:
    """Test cases for runtime edge cases."""

    def test_runtime_with_empty_env_list(self):
        """Test that runtime with empty environment list raises ValidationError."""
        with pytest.raises(
            ValueError, match="At least one env variable must be set in Runtime."
        ):
            Runtime(env=[])

    def test_runtime_with_empty_mounts_list(self):
        """Test that runtime with empty mounts list raises ValidationError."""
        with pytest.raises(
            ValueError, match="At least one mount must be set in Runtime."
        ):
            Runtime(mounts=[])

    def test_runtime_with_env_without_value(self):
        """
        Test that runtime with environment variable without value composes correctly.
        """
        env = Env(key="DEBUG")
        runtime = Runtime(env=[env])
        result = runtime.compose()
        expected = {"remoteEnv": {"DEBUG": None}}
        assert_that(result).is_equal_to(expected)

    def test_runtime_with_volume_mount(self):
        """Test that runtime with volume mount composes correctly."""
        mount = Mount(
            source="data-volume", target="/workspace/data", type=MountType.VOLUME
        )
        runtime = Runtime(mounts=[mount])
        result = runtime.compose()
        expected = {"mounts": ["source=data-volume,target=/workspace/data,type=volume"]}
        assert_that(result).is_equal_to(expected)

    def test_runtime_with_minimal_user_identifier(self):
        """Test that runtime with minimal user identifier is accepted."""
        runtime = Runtime(user="a")
        result = runtime.compose()
        expected = {"remoteUser": "a", "containerUser": "a"}
        assert_that(result).is_equal_to(expected)

    def test_runtime_with_long_user_identifier(self):
        """Test that runtime with long user identifier is accepted."""
        long_user = "a" * 256
        runtime = Runtime(user=long_user)
        result = runtime.compose()
        expected = {"remoteUser": long_user, "containerUser": long_user}
        assert_that(result).is_equal_to(expected)


class TestRuntimeFeatureInheritance:
    """Test cases for Runtime feature inheritance."""

    def test_runtime_feature_name(self):
        """Test that Runtime has the correct feature name."""
        assert_that(Runtime.feature_name()).is_equal_to("runtime")

    def test_runtime_inherits_from_feature(self):
        """Test that Runtime inherits from Feature base class."""
        runtime = Runtime()
        assert_that(runtime).is_instance_of(Runtime)
        # Verify that compose method is implemented
        result = runtime.compose()
        assert_that(result).is_instance_of(dict)

    def test_runtime_compose_method_returns_dict(self):
        """Test that Runtime compose method always returns a dictionary."""
        runtime = Runtime()
        result = runtime.compose()
        assert_that(result).is_instance_of(dict)

        runtime_with_user = Runtime(user="developer")
        result = runtime_with_user.compose()
        assert_that(result).is_instance_of(dict)

        runtime_with_env = Runtime(env=[Env(key="TEST", value="value")])
        result = runtime_with_env.compose()
        assert_that(result).is_instance_of(dict)

        runtime_with_mounts = Runtime(
            mounts=[Mount(source="/test", target="/test", type=MountType.BIND)]
        )
        result = runtime_with_mounts.compose()
        assert_that(result).is_instance_of(dict)
