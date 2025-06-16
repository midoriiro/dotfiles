import configparser
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from devm.main import Format, app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def runner_args():
    return {
        "catch_exceptions": False,
    }


@pytest.fixture
def sources_json_file(tmp_path):
    """Create temporary JSON source files for testing."""
    # Create first source file
    file1 = tmp_path / "source1.json"
    data1 = {"key1": "value1", "key2": "value2"}
    file1.write_text(json.dumps(data1))
    
    # Create second source file
    file2 = tmp_path / "source2.json"
    data2 = {"key3": "value3", "key4": "value4"}
    file2.write_text(json.dumps(data2))
    
    return [file1, file2]

@pytest.fixture
def sources_yaml_file(tmp_path):
    """Create temporary YAML source files for testing."""
    # Create first source file
    file1 = tmp_path / "source1.yaml"
    data1 = {"key1": "value1", "key2": "value2"}
    file1.write_text(yaml.dump(data1))
    
    # Create second source file
    file2 = tmp_path / "source2.yaml"
    data2 = {"key3": "value3", "key4": "value4"}
    file2.write_text(yaml.dump(data2))
    
    return [file1, file2] 

@pytest.fixture
def sources_ini_file(tmp_path):
    """Create temporary INI source files for testing."""
    # Create first source file
    file1 = tmp_path / "source1.ini"
    config1 = configparser.ConfigParser()
    config1["section1"] = {"key1": "value1", "key2": "value2"}
    with open(file1, "w") as f:
        config1.write(f)
    
    # Create second source file
    file2 = tmp_path / "source2.ini"
    config2 = configparser.ConfigParser()
    config2["section2"] = {"key3": "value3", "key4": "value4"}
    with open(file2, "w") as f:
        config2.write(f)
    
    return [file1, file2]

