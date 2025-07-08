import csv
from email.parser import Parser
import hashlib
import logging
from pathlib import Path
import shutil
from typing import Callable, List, Tuple, Union
from email.message import Message

from poexy_core.metadata.fields import MetadataField

logger = logging.getLogger(__name__)

ManifestKey = Union[str, MetadataField]
ManifestValue = Union[str, List[str]]
ManifestStorage = List[Tuple[str, ManifestValue]]
ManifestStorageOperation = Callable[[ManifestStorage], None]


class Manifest:
    def __init__(self, path: Path):
        self.path = path
        self.__storage: ManifestStorage = []

        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def __len__(self):
        return len(self.__storage)
    
    def __iter__(self):
        return iter(self.__storage)
    
    def __getitem__(self, key: ManifestKey) -> ManifestValue:
        return self.get(key)
    
    def __setitem__(self, key: ManifestKey, value: ManifestValue):
        self.set(key, value)

    def __delitem__(self, key: ManifestKey):
        self.delete(key)

    def read(self):
        logger.info(f"Reading {self.path.name} manifest")
        with open(self.path, "r", encoding="utf-8") as file:
            context = file.read()
            parser = Parser()
            data = parser.parsestr(context)
        self.__storage = data.items()
    
    def write(self):
        logger.info(f"Writing {self.path.name} manifest")
        message = Message()
        for k, v in self.__storage:
            if isinstance(v, list) or isinstance(v, tuple):
                for item in v:
                    message.add_header(k, item)
            else:
                message.add_header(k, v)
        with open(self.path, "w", encoding="utf-8") as file:
            file.write(message.as_string())

    def get(self, key: ManifestKey) -> ManifestValue:
        logger.info(f"Getting [{self.path.name}] {key}")
        if isinstance(key, MetadataField):
            key = key.name
        for k, v in self.__storage:
            if k == key:
                return v
        raise KeyError(key)
    
    def set(self, key: ManifestKey, value: ManifestValue):
        if isinstance(value, list) or isinstance(value, tuple):
            log_value = "\n  - ".join(value)
            logger.info(f"Setting [{self.path.name}] {key}: \n  - {log_value}")
        else:
            logger.info(f"Setting [{self.path.name}] {key}: {value}")
        if isinstance(key, MetadataField):
            key = key.name
        for k, _ in self.__storage:
            if k == key:
                raise KeyError(key)
        self.__storage.append((key, value))

    def delete(self, key: ManifestKey):
        logger.info(f"Deleting [{self.path.name}] {key}")
        if isinstance(key, MetadataField):
            key = key.name
        for i, (k, _) in enumerate(self.__storage):
            if k == key:
                del self.__storage[i]
                return
        raise KeyError(key)


ManifestOperation = Callable[[Manifest], None]


class MetadataManifest(Manifest):
    def __init__(self, path: Path):
        super().__init__(path / "METADATA")

class WheelManifest(Manifest):
    def __init__(self, path: Path):
        super().__init__(path / "WHEEL")

class PackageInfoManifest(Manifest):
    def __init__(self, path: Path):
        super().__init__(path / "PKG-INFO")

class Record:
    def __init__(self, path: Path, sha: str, size: int):
        self.path = path
        self.sha = sha
        self.size = size

    def to_relative_path(self, base_path: Path):
        self.path = self.path.relative_to(base_path)

    @staticmethod
    def from_path(path: Path) -> "Record":
        if not path.is_absolute():
            raise ValueError(f"{path} is not an absolute path")
        if not path.is_file():
            raise FileNotFoundError(f"{path} is not a file")
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")
        return Record(
            path, 
            f"sha256={hashlib.sha256(path.read_bytes()).hexdigest()}", 
            path.stat().st_size
        )


ManifestRecordStorage = List[Record]
ManifestRecordStorageOperation = Callable[[ManifestRecordStorage], None]


class RecordManifest:
    def __init__(self, path: Path):
        self.__base_path = path.parent # ./dist-info
        self.__path = path / "RECORD"
        self.__storage: ManifestRecordStorage = []

        if not self.__path.parent.exists():
            self.__path.parent.mkdir(parents=True, exist_ok=True)

    def __len__(self):
        return len(self.__storage)
    
    def __iter__(self):
        return iter(self.__storage)

    def read(self):
        logger.info(f"Reading {self.__path.name} manifest")
        with open(self.__path, "r", encoding="utf-8") as file:
            reader = csv.reader(file, lineterminator="\n")
            for row in reader:
                path = Path(row[0])
                sha = row[1]
                size = int(row[2]) if len(row[2]) > 0 else None
                self.__storage.append(Record(path, sha, size))
    
    def __write(self):
        for record in self.__storage:
            record.to_relative_path(self.__base_path)
        with open(self.__path, "w") as file:
            writer = csv.writer(file, lineterminator="\n")
            rows = []
            for record in self.__storage:
                size = record.size if record.size is not None else ""
                row = [str(record.path), record.sha, size]
                rows.append(row)
            writer.writerows(rows)

    def __copy(self, source: Path, destination: Path):
        if not destination.is_relative_to(self.__base_path):
            raise ValueError(f"Destination {destination} is not relative to {self.__base_path}")
        if not destination.is_dir():
            destination.parent.mkdir(parents=True, exist_ok=True)
        else:
            destination.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, destination)

    def write(self):
        logger.info(f"Writing {self.__path.name} manifest")
        self.__write()

    def add(self, path: Path):
        logger.info(f"Adding [{self.__path.name}]: {path.relative_to(self.__base_path)}")
        self.__storage.append(Record.from_path(path))
    
    def add_self(self):
        logger.info(f"Adding [{self.__path.name}] self: {self.__path.relative_to(self.__base_path)}")
        self.__storage.append(Record(self.__path, None, None))

    def set(self, source: Path, destination: Path):
        logger.info(f"Setting [{self.__path.name}]: {destination.relative_to(self.__base_path)}")
        for record in self.__storage:
            if record.path == destination:
                raise KeyError(destination)
        self.__copy(source, destination)
        self.__storage.append(Record.from_path(destination))
   