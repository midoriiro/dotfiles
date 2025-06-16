import configparser
import io
import json
import logging
from pathlib import Path
from typing import List

import yaml


def merge(a: dict, b: dict) -> dict:
    """
    Recursively merge two dictionaries.
    Handles nested dictionaries and arrays.
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


class FileHandler:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.WARNING)

    def read(self, source: Path):
        raise NotImplementedError
    
    def write(self, data, output=lambda output_data: str):
        raise NotImplementedError

    def merge(self, sources: List[Path]):
        raise NotImplementedError

class JsonHandler(FileHandler):
    def __init__(self):
        super().__init__()

    def read(self, source: Path):
        with open(source, 'r') as f:
            return json.load(f)
        
    def write(self, data, output=lambda output_data: str):
        output(json.dumps(data, indent=2))

    def merge(self, sources: List[Path]):
        merged_data = {}
        for src in sources:
            data = self.read(src)
            merge(merged_data, data)
        return merged_data

class YamlHandler(FileHandler):
    def __init__(self):
        super().__init__()

    def read(self, source: Path):
        with open(source, 'r') as f:
            return yaml.safe_load(f)
        
    def write(self, data, output=lambda output_data: str):
        output(yaml.dump(data, indent=2))

    def merge(self, sources: List[Path]):
        merged_data = {}
        for src in sources:
            data = self.read(src)
            merge(merged_data, data)
        return merged_data
    

class IniHandler(FileHandler):
    def __init__(self):
        super().__init__()

    def read(self, source: Path):
        config = configparser.ConfigParser()
        config.read(source)
        data = {}
        for section in config.sections():
            if section not in data:
                data[section] = {}
            for key, value in config[section].items():
                is_dict = value.startswith('{')
                is_list = value.startswith('[')
                if is_dict or is_list:
                    try:
                        data[section][key] = json.loads(value)
                        continue
                    except json.JSONDecodeError as e:
                        self.logger.warning(
                            f"Failed to parse JSON value in {source}:{section}.{key}. "
                            f"Using raw value instead. Error: {str(e)}"
                        )
                data[section][key] = value
        return data
    
    def write(self, data, output=lambda output_data: str):
        config = configparser.ConfigParser()
        for section, values in data.items():
            if section not in config:
                config[section] = {}
            for key, value in values.items():
                if isinstance(value, (dict, list)):
                    config[section][key] = json.dumps(value)
                else:
                    config[section][key] = value    
        with io.StringIO() as string_io:
            config.write(string_io)
            string_io.seek(0)
            output(string_io.read())

    def merge(self, sources: List[Path]):
        merged_data = {}
        for src in sources:
            data = self.read(src)
            merge(merged_data, data)
        return merged_data
