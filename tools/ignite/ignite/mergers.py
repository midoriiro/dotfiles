import configparser
import io
import json
import logging
from pathlib import Path
from typing import Callable, List

import yaml

from ignite.utils import merge_dicts

class FileMerger:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.WARNING)

    def read(self, source: Path):
        raise NotImplementedError
    
    def write(self, data, writer: Callable[[str], None]):
        raise NotImplementedError

    def merge(self, sources: List[Path]):
        raise NotImplementedError

class JsonFileMerger(FileMerger):
    def __init__(self):
        super().__init__()

    def read(self, source: Path):
        with open(source, 'r') as f:
            return json.load(f)
        
    def write(self, data, writer: Callable[[str], None]):
        writer(json.dumps(data, indent=2))

    def merge(self, sources: List[Path]):
        merged_data = {}
        for src in sources:
            data = self.read(src)
            merge_dicts(merged_data, data)
        return merged_data

class YamlFileMerger(FileMerger):
    def __init__(self):
        super().__init__()

    def read(self, source: Path):
        with open(source, 'r') as f:
            return yaml.safe_load(f)
        
    def write(self, data, writer: Callable[[str], None]):
        writer(yaml.dump(data, indent=2))

    def merge(self, sources: List[Path]):
        merged_data = {}
        for src in sources:
            data = self.read(src)
            merge_dicts(merged_data, data)
        return merged_data
    

class IniFileMerger(FileMerger):
    def __init__(self):
        super().__init__()

    def read(self, source: Path):
        config = configparser.ConfigParser()
        config.read(source)
        data = {}
        sections = [config.default_section, *config.sections()]
        defaults = list(config.defaults().items())
        for section in sections:
            if section not in data:
                data[section] = {}
            if section == config.default_section:
                items = config.items(section)
            else:
                items = [item for item in config.items(section) if item not in defaults]
            for key, value in items:
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
    
    def write(self, data, writer: Callable[[str], None]):
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
            writer(string_io.read())

    def merge(self, sources: List[Path]):
        merged_data = {}
        for src in sources:
            data = self.read(src)
            merge_dicts(merged_data, data)
        return merged_data
