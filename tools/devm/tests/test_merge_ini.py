import configparser
import json
import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devm.main import Format, app, logger


def test_merge_files(runner, sources_ini_file, tmp_path, runner_args):
    """Test merging INI files with default format."""
    output = tmp_path / "output.ini"
    
    result = runner.invoke(
        app, 
        [
            "--output", str(output),
            str(sources_ini_file[0]), 
            str(sources_ini_file[1]), 
        ], 
        **runner_args
    )
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content
    config = configparser.ConfigParser()
    config.read(output)
    assert config["section1"]["key1"] == "value1"
    assert config["section1"]["key2"] == "value2"
    assert config["section2"]["key3"] == "value3"
    assert config["section2"]["key4"] == "value4"


def test_merge_files_with_std_output(runner, sources_ini_file, runner_args):
    """Test merging INI files with stdout output."""
    result = runner.invoke(
        app, 
        [
            "--std-output", 
            str(sources_ini_file[0]), 
            str(sources_ini_file[1])
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    # Verify stdout output
    config = configparser.ConfigParser()
    config.read_string(result.stdout)
    assert config["section1"]["key1"] == "value1"
    assert config["section1"]["key2"] == "value2"
    assert config["section2"]["key3"] == "value3"
    assert config["section2"]["key4"] == "value4"


def test_merge_files_with_explicit_format(runner, sources_ini_file, tmp_path, runner_args):
    """Test merging INI files with explicit INI format."""
    output = tmp_path / "output.ini"
    
    result = runner.invoke(
        app, 
        [
            "--format", "ini",
            "--output", str(output),
            str(sources_ini_file[0]),
            str(sources_ini_file[1]),
        ], 
        **runner_args
    )
    
    assert result.exit_code == 0
    assert output.exists()
    
    # Verify merged content
    config = configparser.ConfigParser()
    config.read(output)
    assert config["section1"]["key1"] == "value1"
    assert config["section1"]["key2"] == "value2"
    assert config["section2"]["key3"] == "value3"
    assert config["section2"]["key4"] == "value4"


def test_merge_files_with_nested_data(runner, tmp_path, runner_args):
    """Test merging INI files with nested data structures."""
    # Create first source file with nested data
    file1 = tmp_path / "nested1.ini"
    config1 = configparser.ConfigParser()
    config1["section1"] = {
        "key1": "value1",
        "array": json.dumps([1, 2, 3]),
        "object": json.dumps({"key2": "value2"}),
        "key4": "value4",
        "key5": "value5",
    }
    with open(file1, 'w') as f:
        config1.write(f)
    
    # Create second source file with nested data
    file2 = tmp_path / "nested2.ini"
    config2 = configparser.ConfigParser()
    config2["section1"] = {
        "key1": "value2",
        "array": json.dumps([4, 5, 6]),
        "object": json.dumps({"key3": "value3"}),
        "key6": "value6",
        "key7": "value7"
    }
    with open(file2, 'w') as f:
        config2.write(f)
    
    output = tmp_path / "nested_output.ini"
    
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
    config = configparser.ConfigParser()
    config.read(output)
    assert config["section1"]["key1"] == "value2"
    assert config["section1"]["array"] == json.dumps([1, 2, 3, 4, 5, 6])
    assert config["section1"]["object"] == json.dumps({"key2": "value2", "key3": "value3"})
    assert config["section1"]["key4"] == "value4"
    assert config["section1"]["key5"] == "value5"
    assert config["section1"]["key6"] == "value6"
    assert config["section1"]["key7"] == "value7"


def test_merge_files_with_conflicting_keys(runner, tmp_path, runner_args):
    """Test merging INI files with conflicting keys."""
    # Create first source file
    file1 = tmp_path / "conflict1.ini"
    config1 = configparser.ConfigParser()
    config1["section1"] = {"key": "value1"}
    with open(file1, 'w') as f:
        config1.write(f)
    
    # Create second source file with same key
    file2 = tmp_path / "conflict2.ini"
    config2 = configparser.ConfigParser()
    config2["section1"] = {"key": "value2"}
    with open(file2, 'w') as f:
        config2.write(f)
    
    output = tmp_path / "conflict_output.ini"
    
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
    config = configparser.ConfigParser()
    config.read(output)
    assert config["section1"]["key"] == "value2"


def test_merge_files_with_malformed_json(runner, tmp_path, runner_args, caplog):
    """Test merging INI files with malformed JSON values."""
    
    caplog.set_level(logging.WARNING)

    # Create first source file with malformed JSON
    file1 = tmp_path / "malformed1.ini"
    config1 = configparser.ConfigParser()
    config1["section1"] = {
        "valid_json": json.dumps({"key": "value"}),
        "malformed_dict": "{key: value}",  # Missing quotes
        "malformed_list": "[1, 2, 3",      # Missing closing bracket
        "regular_value": "normal value"
    }
    with open(file1, 'w') as f:
        config1.write(f)
    
    # Create second source file with valid JSON
    file2 = tmp_path / "malformed2.ini"
    config2 = configparser.ConfigParser()
    config2["section1"] = {
        "valid_json": json.dumps({"key2": "value2"}),
        "malformed_dict": json.dumps({"key": "value"}),  # Valid JSON in second file
        "malformed_list": json.dumps([1, 2, 3]),         # Valid JSON in second file
        "regular_value": "updated value"
    }
    with open(file2, 'w') as f:
        config2.write(f)
    
    output = tmp_path / "malformed_output.ini"
    
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
    assert f"Failed to parse JSON value in {str(file1)}:section1.malformed_dict. Using raw value instead." in caplog.records[0].message
    assert f"Failed to parse JSON value in {str(file1)}:section1.malformed_list. Using raw value instead." in caplog.records[1].message

    assert output.exists()
    
    # Verify merged content
    config = configparser.ConfigParser()
    config.read(output)
    
    # Valid JSON should be merged properly
    assert config["section1"]["valid_json"] == json.dumps({"key": "value", "key2": "value2"})
    
    # Malformed JSON from first file should be overwritten by valid JSON from second file
    assert config["section1"]["malformed_dict"] == json.dumps({"key": "value"})
    assert config["section1"]["malformed_list"] == json.dumps([1, 2, 3])
    
    # Regular value should be updated
    assert config["section1"]["regular_value"] == "updated value" 