from pathlib import Path

import pytest
from typer import BadParameter

from merge.main import Format, validate_path_format


def test_validate_path_format_valid_json(tmp_path):
    """Test validation of a valid JSON file path."""
    test_file = tmp_path / "test.json"
    test_file.touch()
    validate_path_format(test_file)


def test_validate_path_format_valid_yaml(tmp_path):
    """Test validation of a valid YAML file path."""
    test_file = tmp_path / "test.yaml"
    test_file.touch()
    validate_path_format(test_file)


def test_validate_path_format_valid_yml(tmp_path):
    """Test validation of a valid YML file path."""
    test_file = tmp_path / "test.yml"
    test_file.touch()
    validate_path_format(test_file)


def test_validate_path_format_valid_ini(tmp_path):
    """Test validation of a valid INI file path."""
    test_file = tmp_path / "test.ini"
    test_file.touch()
    validate_path_format(test_file)


def test_validate_path_format_invalid_extension(tmp_path):
    """Test validation of a file with invalid extension."""
    test_file = tmp_path / "test.txt"
    test_file.touch()
    with pytest.raises(BadParameter) as exc_info:
        validate_path_format(test_file)
    assert "Unsupported file format" in str(exc_info.value)


def test_validate_path_format_directory(tmp_path):
    """Test validation of a directory path."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    with pytest.raises(BadParameter) as exc_info:
        validate_path_format(test_dir)
    assert "Unsupported file format" in str(exc_info.value)


def test_validate_path_format_nonexistent_file(tmp_path):
    """Test validation of a non-existent file path."""
    test_file = tmp_path / "nonexistent.json"
    validate_path_format(test_file)