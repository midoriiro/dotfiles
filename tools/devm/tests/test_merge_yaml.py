from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from devm.main import Format, app


def test_merge_files(runner, sources_yaml_file, tmp_path, runner_args):
    """Test merging YAML files with default format."""
    output = tmp_path / "output.yaml"
    
    result = runner.invoke(
        app, 
        [
            "--output", str(output),
            str(sources_yaml_file[0]), 
            str(sources_yaml_file[1]), 
        ], 
        **runner_args
    )
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content
    merged_data = yaml.safe_load(output.read_text())
    assert merged_data == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4"
    }


def test_merge_files_with_std_output(runner, sources_yaml_file, runner_args):
    """Test merging YAML files with stdout output."""
    result = runner.invoke(
        app, 
        [
            "--std-output", 
            str(sources_yaml_file[0]), 
            str(sources_yaml_file[1])
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    # Verify stdout output
    output_data = yaml.safe_load(result.stdout)
    assert output_data == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4"
    }


def test_merge_files_with_explicit_format(runner, sources_yaml_file, tmp_path, runner_args):
    """Test merging YAML files with explicit YAML format."""
    output = tmp_path / "output.yaml"
    
    result = runner.invoke(
        app, 
        [
            "--format", "yaml",
            "--output", str(output),
            str(sources_yaml_file[0]),
            str(sources_yaml_file[1]),
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content
    merged_data = yaml.safe_load(output.read_text())
    assert merged_data == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4"
    }


def test_merge_files_with_nested_data(runner, tmp_path, runner_args):
    """Test merging YAML files with nested data structures."""
    # Create first source file with nested data
    file1 = tmp_path / "nested1.yaml"
    data1 = {
        "nested": {
            "key1": "value1",
            "array": [1, 2, 3],
            "object": {
                "key3": "value3",
                "key4": "value4"
            }
        }
    }
    file1.write_text(yaml.dump(data1))
    
    # Create second source file with nested data
    file2 = tmp_path / "nested2.yaml"
    data2 = {
        "nested": {
            "key2": "value2",
            "array": [4, 5, 6],
            "object": {
                "key5": "value5",
                "key6": "value6"
            }
        }
    }
    file2.write_text(yaml.dump(data2))
    
    output = tmp_path / "nested_output.yaml"
    
    result = runner.invoke(
        app, 
        [
            "--output", str(output),
            str(file1), 
            str(file2),
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content
    merged_data = yaml.safe_load(output.read_text())
    assert merged_data == {
        "nested": {
            "key1": "value1",
            "key2": "value2",
            "array": [1, 2, 3, 4, 5, 6],
            "object": {
                "key3": "value3",
                "key4": "value4",
                "key5": "value5",
                "key6": "value6"
            }
        }
    }


def test_merge_files_with_conflicting_keys(runner, tmp_path, runner_args):
    """Test merging YAML files with conflicting keys."""
    # Create first source file
    file1 = tmp_path / "conflict1.yaml"
    data1 = {"key": "value1"}
    file1.write_text(yaml.dump(data1))
    
    # Create second source file with same key
    file2 = tmp_path / "conflict2.yaml"
    data2 = {"key": "value2"}
    file2.write_text(yaml.dump(data2))
    
    output = tmp_path / "conflict_output.yaml"
    
    result = runner.invoke(
        app, 
        [
            "--output", str(output),
            str(file1), 
            str(file2), 
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content (last value should win)
    merged_data = yaml.safe_load(output.read_text())
    assert merged_data == {"key": "value2"} 