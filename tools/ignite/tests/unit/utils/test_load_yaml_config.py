import pytest
from pathlib import Path
from typing import Dict
import yaml
import json
from jsonschema import SchemaError, ValidationError

from ignite.utils import load_yaml_config


class TestLoadYamlConfigFileErrors:
    """Test file-related errors in load_yaml_config function."""

    def test_file_not_found_error(self, tmp_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        non_existent_file = tmp_path / "non_existent.yml"
        schema = {"type": "object"}
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_yaml_config(non_existent_file, schema)
        
        assert str(exc_info.value) == f"Configuration file not found: {non_existent_file}"

    def test_invalid_yaml_file(self, tmp_path):
        """Test that yaml.YAMLError is raised when YAML is invalid."""
        invalid_yaml_file = tmp_path / "invalid.yml"
        invalid_yaml_file.write_text("invalid: yaml: content: [")
        schema = {"type": "object"}
        
        with pytest.raises(yaml.YAMLError):
            load_yaml_config(invalid_yaml_file, schema)

    def test_empty_yaml_file(self, tmp_path):
        """Test loading an empty YAML file."""
        empty_yaml_file = tmp_path / "empty.yml"
        empty_yaml_file.write_text("")
        schema = {"type": "object"}
        
        with pytest.raises(ValidationError):
            load_yaml_config(empty_yaml_file, schema)

class TestLoadYamlConfigSchemaErrors:
    """Test schema-related errors in load_yaml_config function."""

    def test_empty_schema(self, tmp_path):
        """Test that empty schema raises ValidationError."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value")
        empty_schema = {}
        
        with pytest.raises(SchemaError):
            load_yaml_config(yaml_file, empty_schema)

    def test_invalid_schema_type(self, tmp_path):
        """Test that invalid schema type raises ValidationError."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value")
        invalid_schema = {"type": "invalid_type"}
        
        with pytest.raises(SchemaError):
            load_yaml_config(yaml_file, invalid_schema)

    def test_schema_validation_failure(self, tmp_path):
        """Test that schema validation failure raises ValidationError."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value")
        schema = {"type": "object", "properties": {"key": {"type": "integer"}}}
        
        with pytest.raises(ValidationError):
            load_yaml_config(yaml_file, schema)

    def test_required_property_missing(self, tmp_path):
        """Test that missing required property raises ValidationError."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value")
        schema = {
            "type": "object",
            "properties": {"required_key": {"type": "string"}},
            "required": ["required_key"]
        }
        
        with pytest.raises(ValidationError):
            load_yaml_config(yaml_file, schema)


class TestLoadYamlConfigSuccessCases:
    """Test successful cases in load_yaml_config function."""

    def test_valid_yaml_with_simple_schema(self, tmp_path):
        """Test loading valid YAML with simple schema."""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text("key: value")
        schema = {"type": "object"}
        
        result = load_yaml_config(yaml_file, schema)
        assert result == {"key": "value"}

    def test_valid_yaml_with_complex_schema(self, tmp_path):
        """Test loading valid YAML with complex schema."""
        yaml_file = tmp_path / "test.yml"
        yaml_content = """
        name: test
        version: "1.0"
        settings:
          debug: true
          port: 8080
        """
        yaml_file.write_text(yaml_content)
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "settings": {
                    "type": "object",
                    "properties": {
                        "debug": {"type": "boolean"},
                        "port": {"type": "integer"}
                    }
                }
            }
        }
        
        result = load_yaml_config(yaml_file, schema)
        expected = {
            "name": "test",
            "version": "1.0",
            "settings": {
                "debug": True,
                "port": 8080
            }
        }
        assert result == expected

    def test_yaml_with_arrays(self, tmp_path):
        """Test loading YAML with arrays."""
        yaml_file = tmp_path / "test.yml"
        yaml_content = """
        items:
          - name: item1
            value: 10
          - name: item2
            value: 20
        """
        yaml_file.write_text(yaml_content)
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "integer"}
                        }
                    }
                }
            }
        }
        
        result = load_yaml_config(yaml_file, schema)
        expected = {
            "items": [
                {"name": "item1", "value": 10},
                {"name": "item2", "value": 20}
            ]
        }
        assert result == expected


class TestLoadYamlConfigEdgeCases:
    """Test edge cases in load_yaml_config function."""

    def test_yaml_with_comments(self, tmp_path):
        """Test loading YAML with comments."""
        yaml_file = tmp_path / "test.yml"
        yaml_content = """
        # This is a comment
        key: value  # Inline comment
        """
        yaml_file.write_text(yaml_content)
        schema = {"type": "object"}
        
        result = load_yaml_config(yaml_file, schema)
        assert result == {"key": "value"}

    def test_yaml_with_multiline_strings(self, tmp_path):
        """Test loading YAML with multiline strings."""
        yaml_file = tmp_path / "test.yml"
        yaml_content = """
        description: |
          This is a multiline
          string that spans
          multiple lines
        """
        yaml_file.write_text(yaml_content)
        schema = {"type": "object"}
        
        result = load_yaml_config(yaml_file, schema)
        expected = {
            "description": "This is a multiline\nstring that spans\nmultiple lines\n"
        }
        assert result == expected

    def test_yaml_with_null_values(self, tmp_path):
        """Test loading YAML with null values."""
        yaml_file = tmp_path / "test.yml"
        yaml_content = """
        key1: value
        key2: null
        key3: ~
        """
        yaml_file.write_text(yaml_content)
        schema = {"type": "object"}
        
        result = load_yaml_config(yaml_file, schema)
        expected = {"key1": "value", "key2": None, "key3": None}
        assert result == expected
