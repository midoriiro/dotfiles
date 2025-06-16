from pathlib import Path

import pytest
from typer import BadParameter

from devm.main import validate_output


def test_validate_output_valid_path(tmp_path):
    """Test validation of a valid output path."""
    output_path = tmp_path / "output.json"
    result = validate_output(output_path)
    assert result == output_path


def test_validate_output_existing_file(tmp_path):
    """Test validation of an existing output file."""
    output_path = tmp_path / "existing.json"
    output_path.touch()
    
    with pytest.raises(BadParameter) as exc_info:
        validate_output(output_path)
    assert "Output file already exists" in str(exc_info.value)


def test_validate_output_directory(tmp_path):
    """Test validation of a directory path."""
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()
    
    with pytest.raises(BadParameter) as exc_info:
        validate_output(output_dir)
    assert "Output file already exists" in str(exc_info.value)


def test_validate_output_invalid_format(tmp_path):
    """Test validation of a path with invalid file format."""
    output_path = tmp_path / "output.txt"
    
    with pytest.raises(BadParameter) as exc_info:
        validate_output(output_path)
    assert "Unsupported file format" in str(exc_info.value)


def test_validate_output_valid_formats(tmp_path):
    """Test validation of paths with all supported formats."""
    valid_formats = [".json", ".yaml", ".yml", ".ini"]
    
    for fmt in valid_formats:
        output_path = tmp_path / f"output{fmt}"
        result = validate_output(output_path)
        assert result == output_path