from pathlib import Path

import pytest
from typer import BadParameter

from devm.main import validate_sources


def test_validate_sources_valid_files(tmp_path):
    """Test validation of valid source files with same format."""
    # Create test files
    file1 = tmp_path / "test1.json"
    file2 = tmp_path / "test2.json"
    file1.touch()
    file2.touch()
    
    sources = [file1, file2]
    result = validate_sources(sources)
    assert result == sources


def test_validate_sources_insufficient_files(tmp_path):
    """Test validation with less than two source files."""
    file1 = tmp_path / "test1.json"
    file1.touch()
    
    with pytest.raises(BadParameter) as exc_info:
        validate_sources([file1])
    assert "At least two source files must be provided" in str(exc_info.value)


def test_validate_sources_empty_list():
    """Test validation with empty source list."""
    with pytest.raises(BadParameter) as exc_info:
        validate_sources([])
    assert "At least two source files must be provided" in str(exc_info.value)


def test_validate_sources_different_formats(tmp_path):
    """Test validation with files of different formats."""
    file1 = tmp_path / "test1.json"
    file2 = tmp_path / "test2.yaml"
    file1.touch()
    file2.touch()
    
    with pytest.raises(BadParameter) as exc_info:
        validate_sources([file1, file2])
    assert "All source files must have the same format" in str(exc_info.value)


def test_validate_sources_nonexistent_file(tmp_path):
    """Test validation with a non-existent file."""
    file1 = tmp_path / "test1.json"
    file2 = tmp_path / "nonexistent.json"
    file1.touch()
    
    with pytest.raises(BadParameter) as exc_info:
        validate_sources([file1, file2])
    assert "Source file does not exist" in str(exc_info.value)


def test_validate_sources_directory(tmp_path):
    """Test validation with a directory instead of a file."""
    dir1 = tmp_path / "test_dir1"
    dir2 = tmp_path / "test_dir2"
    dir1.mkdir()
    dir2.mkdir()
    
    with pytest.raises(BadParameter) as exc_info:
        validate_sources([dir1, dir2])
    assert "Source path is not a file" in str(exc_info.value)


def test_validate_sources_invalid_format(tmp_path):
    """Test validation with files of invalid format."""
    file1 = tmp_path / "test1.txt"
    file2 = tmp_path / "test2.txt"
    file1.touch()
    file2.touch()
    
    with pytest.raises(BadParameter) as exc_info:
        validate_sources([file1, file2])
    assert "Unsupported file format" in str(exc_info.value) 