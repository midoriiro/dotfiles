import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devm.main import Format, app


def test_merge_files(runner, sources_json_file, tmp_path, runner_args):
    """Test merging JSON files with default format."""
    output = tmp_path / "output.json"
    
    result = runner.invoke(
        app, 
        [
            "--output", str(output),
            str(sources_json_file[0]), 
            str(sources_json_file[1]), 
        ], 
        **runner_args
    )
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content
    merged_data = json.loads(output.read_text())
    assert merged_data == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4"
    }


def test_merge_files_with_std_output(runner, sources_json_file, runner_args):
    """Test merging JSON files with stdout output."""
    result = runner.invoke(
        app, 
        [
            "--std-output", 
            str(sources_json_file[0]), 
            str(sources_json_file[1])
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    # Verify stdout output
    output_data = json.loads(result.stdout)
    assert output_data == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4"
    }


def test_merge_files_with_explicit_format(runner, sources_json_file, tmp_path, runner_args):
    """Test merging JSON files with explicit JSON format."""
    output = tmp_path / "output.json"
    
    result = runner.invoke(
        app, 
        [
            "--format", "json",
            "--output", str(output),
            str(sources_json_file[0]),
            str(sources_json_file[1]),
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content
    merged_data = json.loads(output.read_text())
    assert merged_data == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4"
    }


def test_merge_files_with_nested_data(runner, tmp_path, runner_args):
    """Test merging JSON files with nested data structures."""
    # Create first source file with nested data
    file1 = tmp_path / "nested1.json"
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
    file1.write_text(json.dumps(data1))
    
    # Create second source file with nested data
    file2 = tmp_path / "nested2.json"
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
    file2.write_text(json.dumps(data2))
    
    output = tmp_path / "nested_output.json"
    
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
    merged_data = json.loads(output.read_text())
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
    """Test merging JSON files with conflicting keys."""
    # Create first source file
    file1 = tmp_path / "conflict1.json"
    data1 = {"key": "value1"}
    file1.write_text(json.dumps(data1))
    
    # Create second source file with same key
    file2 = tmp_path / "conflict2.json"
    data2 = {"key": "value2"}
    file2.write_text(json.dumps(data2))
    
    output = tmp_path / "conflict_output.json"
    
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
    merged_data = json.loads(output.read_text())
    assert merged_data == {"key": "value2"} 