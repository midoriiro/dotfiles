from pathlib import Path
from typing import Dict

import yaml
import json
from jsonschema import SchemaError, ValidationError, validate

def load_yaml_config(
    file_path: Path, schema: Dict
) -> Dict:
    """
    Load and validate a YAML configuration file.

    Args:
        file_path (Path): Path to the YAML configuration file.
        schema (Dict): JSON schema to validate the configuration against.

    Returns:
        Dict: Validated configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML is invalid.
        json.JSONDecodeError: If the schema JSON is invalid.
        ValidationError: If the configuration does not match the schema.
    """
    
    if len(schema.keys()) == 0:
        raise SchemaError("Schema is empty")

    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, "r") as f:
        config_data = yaml.safe_load(f)

    validate(instance=config_data, schema=schema)
    return config_data

def merge_dicts(a: Dict, b: Dict) -> None:
    """
    Recursively merge two dictionaries.
    
    This function performs a deep merge of two dictionaries, handling nested
    dictionaries and lists. The merge process modifies the first dictionary
    in-place and returns it. For nested dictionaries, the function recursively
    merges their contents. For lists, the function concatenates them.
    
    Args:
        a (Dict): The target dictionary to merge into. This dictionary will be
                  modified in-place during the merge process.
        b (Dict): The source dictionary whose contents will be merged into 'a'.
    
    Returns:
        None: The function modifies the first dictionary in-place.
    
    Note:
        - The function modifies the first dictionary in-place
        - Nested dictionaries are merged recursively
        - Lists are concatenated (not merged element-wise)
        - Other data types are overwritten if they exist in both dictionaries
        - Keys that only exist in 'b' are added to 'a'
    
    Example:
        >>> a = {'x': 1, 'y': {'a': 1, 'b': 2}, 'z': [1, 2]}
        >>> b = {'y': {'b': 3, 'c': 4}, 'z': [3, 4], 'w': 5}
        >>> merge_dicts(a, b)
        {'x': 1, 'y': {'a': 1, 'b': 3, 'c': 4}, 'z': [1, 2, 3, 4], 'w': 5}
    """
    stack = [(a, b)]

    while stack:
        current_a, current_b = stack.pop()
        for key, value in current_b.items():
            if key in current_a:
                if isinstance(current_a[key], dict) and isinstance(value, dict):
                    stack.append((current_a[key], value))
                elif isinstance(current_a[key], list) and isinstance(value, list):
                    current_a[key] = current_a[key] + value
                else:
                    current_a[key] = value
            else:
                current_a[key] = value