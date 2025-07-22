import pytest
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.common import Identifier
from ignite.models.container import Build


class TestValidBuild:
    """Test cases for valid build configurations."""

    @pytest.mark.parametrize(
        "container_file",
        [
            "Dockerfile",
            "Containerfile",
            "docker/Dockerfile",
            "build/Containerfile",
            "dockerfile",
            "containerfile",
        ],
    )
    def test_valid_build_with_container_file_only(self, container_file):
        """Test that valid build configurations with only container_file are accepted."""
        build = Build(container_file=container_file)
        assert_that(build.container_file).is_equal_to(container_file)
        assert_that(build.context).is_none()
        assert_that(build.target).is_none()

    @pytest.mark.parametrize(
        "container_file,context",
        [
            ("Dockerfile", "src"),
            ("Containerfile", "app"),
            ("docker/Dockerfile", "backend"),
            ("build/Containerfile", "frontend"),
        ],
    )
    def test_valid_build_with_container_file_and_context(self, container_file, context):
        """Test that valid build configurations with container_file and context are accepted."""
        build = Build(container_file=container_file, context=context)
        assert_that(build.container_file).is_equal_to(container_file)
        assert_that(build.context).is_equal_to(context)
        assert_that(build.target).is_none()

    @pytest.mark.parametrize(
        "container_file,target",
        [
            ("Dockerfile", "development"),
            ("Containerfile", "production"),
            ("docker/Dockerfile", "test"),
            ("build/Containerfile", "staging"),
        ],
    )
    def test_valid_build_with_container_file_and_target(self, container_file, target):
        """Test that valid build configurations with container_file and target are accepted."""
        build = Build(container_file=container_file, target=target)
        assert_that(build.container_file).is_equal_to(container_file)
        assert_that(build.context).is_none()
        assert_that(build.target).is_equal_to(target)

    def test_valid_build_with_all_parameters(self):
        """Test that valid build configurations with all parameters are accepted."""
        build = Build(container_file="Dockerfile", context="src", target="production")
        assert_that(build.container_file).is_equal_to("Dockerfile")
        assert_that(build.context).is_equal_to("src")
        assert_that(build.target).is_equal_to("production")


class TestBuildValidation:
    """Test cases for build validation rules."""

    def test_build_without_container_file(self):
        """Test that build configurations without container_file are rejected."""
        with pytest.raises(ValidationError, match="Field required"):
            Build()

    def test_build_with_empty_container_file(self):
        """Test that build configurations with empty container_file are rejected."""
        with pytest.raises(ValidationError, match="Path cannot be whitespace-only"):
            Build(container_file="")

    def test_build_with_invalid_container_file_pattern(self):
        """Test that build configurations with invalid container_file patterns are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Build(container_file="invalid@file")

    def test_build_with_too_long_container_file(self):
        """Test that build configurations with container_file longer than 256 characters are rejected."""
        long_file = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 items"):
            Build(container_file=long_file)

    def test_build_with_empty_context(self):
        """Test that build configurations with empty context are rejected."""
        with pytest.raises(ValidationError, match="Path cannot be whitespace-only"):
            Build(container_file="Dockerfile", context="")

    def test_build_with_invalid_context_pattern(self):
        """Test that build configurations with invalid context patterns are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Build(container_file="Dockerfile", context="invalid@context")

    def test_build_with_too_long_context(self):
        """Test that build configurations with context longer than 256 characters are rejected."""
        long_context = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 items"):
            Build(container_file="Dockerfile", context=long_context)

    def test_build_with_invalid_target_pattern(self):
        """Test that build configurations with invalid target patterns are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            Build(container_file="Dockerfile", target="invalid@target")

    def test_build_with_too_long_target(self):
        """Test that build configurations with target longer than 256 characters are rejected."""
        long_target = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            Build(container_file="Dockerfile", target=long_target)


class TestBuildCompose:
    """Test cases for build composition."""

    def test_compose_build_with_container_file_only(self):
        """Test that build with only container_file is composed correctly."""
        build = Build(container_file="Dockerfile")
        result = build.compose()
        expected = {"build": {"dockerFile": "Dockerfile"}}
        assert_that(result).is_equal_to(expected)

    def test_compose_build_with_container_file_and_context(self):
        """Test that build with container_file and context is composed correctly."""
        build = Build(container_file="Dockerfile", context="src")
        result = build.compose()
        expected = {"build": {"dockerFile": "Dockerfile", "context": "src"}}
        assert_that(result).is_equal_to(expected)

    def test_compose_build_with_container_file_and_target(self):
        """Test that build with container_file and target is composed correctly."""
        build = Build(container_file="Dockerfile", target="production")
        result = build.compose()
        expected = {"build": {"dockerFile": "Dockerfile", "target": "production"}}
        assert_that(result).is_equal_to(expected)

    def test_compose_build_with_all_parameters(self):
        """Test that build with all parameters is composed correctly."""
        build = Build(container_file="Dockerfile", context="src", target="production")
        result = build.compose()
        expected = {
            "build": {
                "dockerFile": "Dockerfile",
                "context": "src",
                "target": "production",
            }
        }
        assert_that(result).is_equal_to(expected)

    def test_compose_build_with_context_and_target_only(self):
        """Test that build with context and target (no container_file) raises ValidationError."""
        with pytest.raises(ValidationError, match="Field required"):
            Build(context="src", target="production")


class TestBuildEdgeCases:
    """Test cases for build edge cases."""

    def test_build_with_minimal_valid_container_file(self):
        """Test that build with minimal valid container_file is accepted."""
        build = Build(container_file="a")
        assert_that(build.container_file).is_equal_to("a")
        assert_that(build.context).is_none()
        assert_that(build.target).is_none()

    def test_build_with_long_valid_container_file(self):
        """Test that build with long valid container_file is accepted."""
        long_file = "a" * 256
        build = Build(container_file=long_file)
        assert_that(build.container_file).is_equal_to(long_file)
        assert_that(build.context).is_none()
        assert_that(build.target).is_none()

    def test_build_with_minimal_valid_context(self):
        """Test that build with minimal valid context is accepted."""
        build = Build(container_file="Dockerfile", context="a")
        assert_that(build.container_file).is_equal_to("Dockerfile")
        assert_that(build.context).is_equal_to("a")
        assert_that(build.target).is_none()

    def test_build_with_long_valid_context(self):
        """Test that build with long valid context is accepted."""
        long_context = "a" * 256
        build = Build(container_file="Dockerfile", context=long_context)
        assert_that(build.container_file).is_equal_to("Dockerfile")
        assert_that(build.context).is_equal_to(long_context)
        assert_that(build.target).is_none()

    def test_build_with_minimal_valid_target(self):
        """Test that build with minimal valid target is accepted."""
        build = Build(container_file="Dockerfile", target="a")
        assert_that(build.container_file).is_equal_to("Dockerfile")
        assert_that(build.context).is_none()
        assert_that(build.target).is_equal_to("a")

    def test_build_with_long_valid_target(self):
        """Test that build with long valid target is accepted."""
        long_target = "a" * 256
        build = Build(container_file="Dockerfile", target=long_target)
        assert_that(build.container_file).is_equal_to("Dockerfile")
        assert_that(build.context).is_none()
        assert_that(build.target).is_equal_to(long_target)

    def test_build_with_special_characters_in_container_file(self):
        """Test that build with valid special characters in container_file is accepted."""
        build = Build(container_file="docker-file_123")
        assert_that(build.container_file).is_equal_to("docker-file_123")
        assert_that(build.context).is_none()
        assert_that(build.target).is_none()

    def test_build_with_special_characters_in_context(self):
        """Test that build with valid special characters in context is accepted."""
        build = Build(container_file="Dockerfile", context="src-folder_123")
        assert_that(build.container_file).is_equal_to("Dockerfile")
        assert_that(build.context).is_equal_to("src-folder_123")
        assert_that(build.target).is_none()

    def test_build_with_special_characters_in_target(self):
        """Test that build with valid special characters in target is accepted."""
        build = Build(container_file="Dockerfile", target="build-stage_123")
        assert_that(build.container_file).is_equal_to("Dockerfile")
        assert_that(build.context).is_none()
        assert_that(build.target).is_equal_to("build-stage_123")

    def test_build_with_whitespace_only_container_file(self):
        """Test that build with whitespace-only container_file is rejected."""
        with pytest.raises(ValidationError, match="Path cannot be whitespace-only"):
            Build(container_file="   ")

    def test_build_with_whitespace_only_context(self):
        """Test that build with whitespace-only context is rejected."""
        with pytest.raises(ValidationError, match="Path cannot be whitespace-only"):
            Build(container_file="Dockerfile", context="   ")


class TestBuildFeatureInheritance:
    """Test cases for Build feature inheritance."""

    def test_build_feature_name(self):
        """Test that Build has the correct feature name."""
        assert_that(Build.feature_name()).is_equal_to("build")

    def test_build_inherits_from_feature(self):
        """Test that Build inherits from Feature base class."""
        build = Build(container_file="Dockerfile")
        assert_that(build).is_instance_of(Build)
        # Verify that compose method is implemented
        result = build.compose()
        assert_that(result).is_instance_of(dict)

    def test_build_compose_returns_dict(self):
        """Test that Build compose method returns a dictionary."""
        build = Build(container_file="Dockerfile")
        result = build.compose()
        assert_that(result).is_instance_of(dict)
        assert_that(result).contains_key("build")
        assert_that(result["build"]).is_instance_of(dict)


class TestBuildAlias:
    """Test cases for Build field aliases."""

    def test_build_deserialization_uses_alias(self):
        """Test that Build deserialization uses the container-file alias."""
        build = Build(container_file="Dockerfile")
        serialized = build.model_dump(by_alias=True)
        deserialized = Build.model_validate(serialized, by_alias=True)
        assert_that(deserialized.container_file).is_equal_to("Dockerfile")

    def test_build_serialization_uses_alias(self):
        """Test that Build serialization uses the container-file alias."""
        build = Build(container_file="Dockerfile")
        serialized = build.model_dump(by_alias=True)
        assert_that(serialized).contains_key("container-file")
        assert_that(serialized["container-file"]).is_equal_to("Dockerfile")
        assert_that(serialized).does_not_contain_key("container_file")

    def test_build_serialization_with_all_fields(self):
        """Test that Build serialization uses aliases for all fields with aliases."""
        build = Build(container_file="Dockerfile", context="src", target="production")
        serialized = build.model_dump(by_alias=True)
        assert_that(serialized).contains_key("container-file")
        assert_that(serialized["container-file"]).is_equal_to("Dockerfile")
        assert_that(serialized).contains_key("context")
        assert_that(serialized["context"]).is_equal_to("src")
        assert_that(serialized).contains_key("target")
        assert_that(serialized["target"]).is_equal_to("production")

    def test_build_construction_with_python_name(self):
        """Test that Build construction works with the Python field name."""
        build = Build(container_file="Dockerfile")
        assert_that(build.container_file).is_equal_to("Dockerfile")

    def test_build_construction_with_alias(self):
        """Test that Build construction works with the alias name."""
        build = Build(**{"container-file": "Dockerfile"})
        assert_that(build.container_file).is_equal_to("Dockerfile")

    def test_build_construction_with_both_names(self):
        """Test that Build construction works with both Python name and alias."""
        # Both should work
        build1 = Build(container_file="Dockerfile")
        build2 = Build(**{"container-file": "Dockerfile"})
        assert_that(build1.container_file).is_equal_to("Dockerfile")
        assert_that(build2.container_file).is_equal_to("Dockerfile")
