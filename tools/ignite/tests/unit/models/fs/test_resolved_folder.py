import configparser
import json
from pathlib import Path
from typing import Dict

import pytest
import yaml
from assertpy import assert_that
from pydantic import ValidationError

from ignite.models.fs import FileTemplateVariables, ResolvedFile, ResolvedFolder


@pytest.fixture
def json_source_files(user_context: Path) -> Dict[str, Path]:
    """Create temporary JSON source files for testing."""
    files = {}

    # First JSON file
    file1 = user_context / "source1.json"
    data1 = {
        "name": "${project-name}",
        "version": "1.0.0",
        "dependencies": {"requests": "2.28.0"},
    }
    file1.write_text(json.dumps(data1, indent=2))
    files["source1"] = file1

    # Second JSON file
    file2 = user_context / "source2.json"
    data2 = {
        "version": "2.0.0",
        "dependencies": {"pytest": "7.0.0"},
        "scripts": {"test": "pytest"},
    }
    file2.write_text(json.dumps(data2, indent=2))
    files["source2"] = file2

    return files


@pytest.fixture
def yaml_source_files(user_context: Path) -> Dict[str, Path]:
    """Create temporary YAML source files for testing."""
    files = {}

    # First YAML file
    file1 = user_context / "source1.yaml"
    data1 = {
        "name": "${project-name}",
        "version": "1.0.0",
        "dependencies": {"requests": "2.28.0"},
    }
    file1.write_text(yaml.dump(data1, indent=2))
    files["source1"] = file1

    # Second YAML file
    file2 = user_context / "source2.yaml"
    data2 = {
        "version": "2.0.0",
        "dependencies": {"pytest": "7.0.0"},
        "scripts": {"test": "pytest"},
    }
    file2.write_text(yaml.dump(data2, indent=2))
    files["source2"] = file2

    return files


@pytest.fixture
def ini_source_files(user_context: Path) -> Dict[str, Path]:
    """Create temporary INI source files for testing."""
    files = {}

    # First INI file
    file1 = user_context / "source1.ini"
    config1 = configparser.ConfigParser()
    config1["DEFAULT"] = {"name": "${project-name}", "version": "1.0.0"}
    config1["dependencies"] = {"requests": "2.28.0"}
    with open(file1, "w") as f:
        config1.write(f)
    files["source1"] = file1

    # Second INI file
    file2 = user_context / "source2.ini"
    config2 = configparser.ConfigParser()
    config2["DEFAULT"] = {"version": "2.0.0"}
    config2["dependencies"] = {"pytest": "7.0.0"}
    config2["scripts"] = {"test": "pytest"}
    with open(file2, "w") as f:
        config2.write(f)
    files["source2"] = file2

    return files


@pytest.fixture
def template_variables() -> FileTemplateVariables:
    """Create FileTemplateVariables instance for testing."""
    return FileTemplateVariables(project_name="my-test-project")


class TestResolvedFolderCreation:
    """Test ResolvedFolder creation and validation."""

    def test_creation_with_valid_data(self):
        """Test ResolvedFolder creation with valid data."""
        sources = ["/path/to/source1.json", "/path/to/source2.json"]
        destination = "/path/to/destination.json"

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)

        assert_that(resolved_folder.sources).is_equal_to(sources)
        assert_that(resolved_folder.destination).is_equal_to(destination)

    def test_creation_with_empty_sources(self):
        """Test ResolvedFolder creation fails with empty sources list."""
        sources = []
        destination = "/path/to/destination.json"

        with pytest.raises(ValidationError, match="should have at least 1"):
            ResolvedFolder(sources=sources, destination=destination)


class TestResolvedFolderResolveFormats:
    """Test ResolvedFolder resolve method with different file formats."""

    def test_resolve_json_files(
        self,
        json_source_files: Dict[str, Path],
        template_variables: FileTemplateVariables,
    ):
        """Test ResolvedFolder resolve method with JSON files."""
        sources = [str(json_source_files["source1"]), str(json_source_files["source2"])]
        destination = "/path/to/destination.json"

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)
        result = resolved_folder.resolve(template_variables)

        assert_that(result).is_instance_of(ResolvedFile)
        assert_that(result.path).is_equal_to(destination)

        # Parse the content to verify it's valid JSON
        content_data = json.loads(result.content)

        # Check that data was merged correctly
        assert_that(content_data["name"]).is_equal_to(template_variables.project_name)
        assert_that(content_data["version"]).is_equal_to(
            "2.0.0"
        )  # Second file overwrites first
        assert_that(content_data["dependencies"]).is_equal_to(
            {"requests": "2.28.0", "pytest": "7.0.0"}
        )
        assert_that(content_data["scripts"]).is_equal_to({"test": "pytest"})

    def test_resolve_yaml_files(
        self,
        yaml_source_files: Dict[str, Path],
        template_variables: FileTemplateVariables,
    ):
        """Test ResolvedFolder resolve method with YAML files."""
        sources = [str(yaml_source_files["source1"]), str(yaml_source_files["source2"])]
        destination = "/path/to/destination.yaml"

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)
        result = resolved_folder.resolve(template_variables)

        assert_that(result).is_instance_of(ResolvedFile)
        assert_that(result.path).is_equal_to(destination)

        # Parse the content to verify it's valid YAML
        content_data = yaml.safe_load(result.content)

        # Check that data was merged correctly
        assert_that(content_data["name"]).is_equal_to(template_variables.project_name)
        assert_that(content_data["version"]).is_equal_to(
            "2.0.0"
        )  # Second file overwrites first
        assert_that(content_data["dependencies"]).is_equal_to(
            {"requests": "2.28.0", "pytest": "7.0.0"}
        )
        assert_that(content_data["scripts"]).is_equal_to({"test": "pytest"})

    def test_resolve_ini_files(
        self,
        ini_source_files: Dict[str, Path],
        template_variables: FileTemplateVariables,
    ):
        """Test ResolvedFolder resolve method with INI files."""
        sources = [str(ini_source_files["source1"]), str(ini_source_files["source2"])]
        destination = "/path/to/destination.ini"

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)
        result = resolved_folder.resolve(template_variables)

        assert_that(result).is_instance_of(ResolvedFile)
        assert_that(result.path).is_equal_to(destination)

        # Parse the content to verify it's valid INI
        config = configparser.ConfigParser()
        config.read_string(result.content)

        # Check that data was merged correctly
        assert_that(config["DEFAULT"]["name"]).is_equal_to(
            template_variables.project_name
        )
        assert_that(config["DEFAULT"]["version"]).is_equal_to(
            "2.0.0"
        )  # Second file overwrites first
        assert_that(config["dependencies"]["requests"]).is_equal_to("2.28.0")
        assert_that(config["dependencies"]["pytest"]).is_equal_to("7.0.0")
        assert_that(config["scripts"]["test"]).is_equal_to("pytest")

    def test_resolve_with_yml_extension(
        self,
        yaml_source_files: Dict[str, Path],
        template_variables: FileTemplateVariables,
    ):
        """Test ResolvedFolder resolve method with .yml extension."""
        sources = [str(yaml_source_files["source1"])]
        destination = "/path/to/destination.yml"  # .yml extension

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)
        result = resolved_folder.resolve(template_variables)

        assert_that(result).is_instance_of(ResolvedFile)
        assert_that(result.path).is_equal_to(destination)

        # Parse the content to verify it's valid YAML
        content_data = yaml.safe_load(result.content)
        assert_that(content_data["name"]).is_equal_to(template_variables.project_name)
        assert_that(content_data["version"]).is_equal_to("1.0.0")


class TestResolvedFolderResolveScenarios:
    """Test ResolvedFolder resolve method with different scenarios."""

    def test_resolve_with_single_source(
        self,
        json_source_files: Dict[str, Path],
        template_variables: FileTemplateVariables,
    ):
        """Test ResolvedFolder resolve method with single source file."""
        sources = [str(json_source_files["source1"])]
        destination = "/path/to/destination.json"

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)
        result = resolved_folder.resolve(template_variables)

        assert_that(result).is_instance_of(ResolvedFile)
        assert_that(result.path).is_equal_to(destination)

        # Parse the content to verify it's valid JSON
        content_data = json.loads(result.content)
        assert_that(content_data["name"]).is_equal_to(template_variables.project_name)
        assert_that(content_data["version"]).is_equal_to("1.0.0")
        assert_that(content_data["dependencies"]).is_equal_to({"requests": "2.28.0"})

    def test_resolve_with_none_variables(self, json_source_files: Dict[str, Path]):
        """Test ResolvedFolder resolve method with None variables."""
        sources = [str(json_source_files["source1"])]
        destination = "/path/to/destination.json"

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)

        with pytest.raises(ValueError, match="Variables cannot be None."):
            resolved_folder.resolve(None)


class TestResolvedFolderErrorHandling:
    """Test ResolvedFolder error handling scenarios."""

    def test_resolve_with_unsupported_extension(
        self,
        json_source_files: Dict[str, Path],
        template_variables: FileTemplateVariables,
    ):
        """Test ResolvedFolder resolve method with unsupported file extension."""
        sources = [str(json_source_files["source1"])]
        destination = "/path/to/destination.txt"  # Unsupported extension

        resolved_folder = ResolvedFolder(sources=sources, destination=destination)

        with pytest.raises(ValueError, match="Unsupported file extension: .txt"):
            resolved_folder.resolve(template_variables)
