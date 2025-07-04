import contextlib
import csv
from enum import Enum
import hashlib
import logging
import sys
from pathlib import Path
import shutil
import sysconfig
from tempfile import TemporaryDirectory
from typing import Callable, Generator, List, Optional, Tuple, Union
import zipfile
from email.message import Message
from email.parser import Parser

from poexy.safe_print import safe_print_info, safe_print_start, safe_print_success

logger = logging.getLogger(__name__)

ManifestStorage = List[Tuple[str, str]]
ManifestStorageOperation = Callable[[ManifestStorage], None]


class Manifest:
    def __init__(self, path: Path):
        self.__path = path
        self.__operations: List[ManifestStorageOperation] = []
    
    def __read(self) -> ManifestStorage:
        with open(self.__path, "r", encoding="utf-8") as file:
            storage = file.read()
        data = Parser().parsestr(storage)
        return data.items()
    
    def __write(self, storage: ManifestStorage):
        message = Message()
        for k, v in storage:
            message.add_header(k, v)
        with open(self.__path, "w", encoding="utf-8") as file:
            file.write(message.as_string())

    def build(self):
        storage = self.__read()
        for operation in self.__operations:
            operation(storage)
        self.__write(storage)

    def get(self, key: str, callback: Callable[[str], None]):
        def operation(storage: ManifestStorage):
            for k, v in storage:
                if k == key:
                    callback(v)
                    return
            raise KeyError(key)
        self.__operations.append(operation)

    def find_and_delete(self, filter: Callable[[str, str], bool]):
        indexes_to_delete = []
        def operation(storage: ManifestStorage):
            for i, (k, v) in zip(range(len(storage)), storage):
                if filter(k, v):
                    indexes_to_delete.append(i)
            for i in reversed(indexes_to_delete):
                del storage[i]
        self.__operations.append(operation)
    
    def set(self, key: str, value: str):
        def operation(storage: ManifestStorage):
            for k, _ in storage:
                if k == key:
                    raise KeyError(key)
            storage.append((key, value))
        self.__operations.append(operation)

    def replace(self, key: str, value: str):
        def operation(storage: ManifestStorage):
            for i, (k, _) in zip(range(len(storage)), storage):
                if k == key:
                    storage[i] = (key, value)
                    return
            raise KeyError(key)
        self.__operations.append(operation)

    def replace_or_set(self, key: str, value: str):
        def operation(storage: ManifestStorage):
            for i, (k, _) in zip(range(len(storage)), storage):
                if k == key:
                    storage[i] = (key, value)
                    return
            storage.append((key, value))
        self.__operations.append(operation)

    def delete(self, key: str, all: bool = False):
        def operation(storage: ManifestStorage):
            count = 0
            indexes_to_delete = []
            for i, (k, v) in zip(range(len(storage)), storage):
                if k == key:
                    indexes_to_delete.append(i)
                    count += 1
                    if not all:
                        break
            for i in reversed(indexes_to_delete):
                del storage[i]
            if count == 0:
                raise KeyError(key)
        self.__operations.append(operation)


ManifestOperation = Callable[[Manifest], None]


class MetadataManifest:
    def __init__(self, path: Path):
        self.path = path
        self.__manifest = Manifest(path)
        self.__operations: List[ManifestOperation] = []

    def build(self) -> bool:
        for operation in self.__operations:
            operation(self.__manifest)
        self.__manifest.build()
        return len(self.__operations) > 0
    
    def set_required_python_version(self, value: str):
        def operation(manifest: Manifest):
            manifest.replace_or_set("Requires-Python", value)
        self.__operations.append(operation)

    def set_platform(self, value: str):
        def operation(manifest: Manifest):
            manifest.replace_or_set("Platform", value)
        self.__operations.append(operation)

    def set_supported_platform(self, value: str):
        def operation(manifest: Manifest):
            manifest.replace_or_set("Supported-Platform", value)
        self.__operations.append(operation)

    def delete_requires_dist(self):
        def operation(manifest: Manifest):
            manifest.delete("Requires-Dist", all=True)
        self.__operations.append(operation)

    def delete_classifiers(self, key: str, value: Callable[[str], bool]):
        def operation(manifest: Manifest):
            manifest.find_and_delete(lambda k, v: k == key and value(v))
        self.__operations.append(operation)

class WheelManifest:
    def __init__(self, path: Path):
        self.path = path
        self.__manifest = Manifest(path)
        self.__operations: List[ManifestOperation] = []

    def build(self) -> bool:
        for operation in self.__operations:
            operation(self.__manifest)
        self.__manifest.build()
        return len(self.__operations) > 0

    def set_root_is_purelib(self, value: bool):
        def operation(manifest: Manifest):
            manifest.replace("Root-Is-Purelib", "true" if value else "false")
        self.__operations.append(operation)

    def set_tag(self, value: str):
        def operation(manifest: Manifest):
            manifest.replace("Tag", value)
        self.__operations.append(operation)


class Record:
    def __init__(self, path: Path, sha: str, size: int):
        self.path = path
        self.sha = sha
        self.size = size

    def to_relative_path(self, base_path: Path):
        self.path = self.path.relative_to(base_path)

    def delete(self):
        if self.path.exists() and self.path.is_file():
            self.path.unlink()
        else:
            raise FileNotFoundError(self.path)

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
        self.__base_path = path.parent.parent # /dist-info/..
        self.__path = path
        self.__operations: List[ManifestRecordStorageOperation] = []

    def __read(self) -> List[Record]:
        with open(self.__path, "r") as file:
            records = csv.reader(file)
            records = [Record(Path(line[0]), line[1], line[2]) for line in records]
            for record in records:
                record.path = self.__base_path / record.path
            return records
    
    def __write(self, records: List[Record]):
        for record in records:
            record.to_relative_path(self.__base_path)
        with open(self.__path, "w") as file:
            writer = csv.writer(file, lineterminator="\n")
            rows = [[str(record.path), record.sha, str(record.size)] for record in records]
            writer.writerows(rows)

    def __copy(self, source: Path, destination: Path):
        if not destination.is_relative_to(self.__base_path):
            raise ValueError(f"Destination {destination} is not relative to {self.__base_path}")
        if not destination.is_dir():
            destination.parent.mkdir(parents=True, exist_ok=True)
        else:
            destination.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, destination)

    def __delete(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(path)
        if not path.is_relative_to(self.__base_path):
            raise ValueError(f"Path {path} is not relative to {self.__base_path}")

    def build(self):
        records = self.__read()
        for operation in self.__operations:
            operation(records)
        for record in records:
            print(record.path, record.sha, record.size)
        self.__write(records)

    def get(self, path: Path) -> Record:
        def operation(records: ManifestRecordStorage):
            for record in records:
                if record.path == path:
                    return record
            raise KeyError(path)
        self.__operations.append(operation)

    def set(self, source: Path, destination: Path):
        def operation(records: ManifestRecordStorage):
            for record in records:
                if record.path == destination:
                    raise KeyError(destination)
            self.__copy(source, destination)
            records.append(Record.from_path(destination))
        self.__operations.append(operation)

    def replace(self, source: Path, destination: Path,):
        def operation(records: ManifestRecordStorage):
            record_path = self.__base_path / destination / source.name
            for i, record in zip(range(len(records)), records):
                if record.path == record_path:
                    self.__copy(source, record_path)
                    records[i] = Record.from_path(record_path)
                    return
            raise KeyError(destination)
        self.__operations.append(operation)
        
    def replace_in_place(self, path: Path):
        def operation(records: ManifestRecordStorage):
            for i, record in zip(range(len(records)), records):
                if record.path == path:
                    records[i] = Record.from_path(path)
                    return
        self.__operations.append(operation)

    def delete(self, path: Path):
        def operation(records: ManifestRecordStorage):
            for record in records:
                if record.path == path:
                    records.remove(record)
                    self.__delete(path)
                    record.delete()
                    return
            raise KeyError(path)
        self.__operations.append(operation)
        
class Manifests:
    def __init__(self, path: Path):
        self.metadata: MetadataManifest = MetadataManifest(path / "METADATA")
        self.wheel: WheelManifest = WheelManifest(path / "WHEEL")
        self.record: RecordManifest = RecordManifest(path / "RECORD")
    
    def build(self):
        is_metadata_changed = self.metadata.build()
        is_wheel_changed = self.wheel.build()
        if is_metadata_changed:
            self.record.replace_in_place(self.metadata.path)
        if is_wheel_changed:
            self.record.replace_in_place(self.wheel.path)
        self.record.build()


class WheelDataSubFolder(str, Enum):
    PURELIB = "purelib"
    PLATLIB = "platlib"
    HEADERS = "headers"
    SCRIPTS = "scripts"
    DATA = "data"


class WheelMetadata:
    def __init__(self, path: Path, name: str, version: str):
        self.path: Path = path
        self.name: str = name
        self.version: str = version
        self.tag: str = self.__tag()
        self.platform: str = sysconfig.get_platform()
        self.archive_filename: Path = self.__archive_filename()
        self.dist_info_folder: Path = self.__dist_info_folder()
        self.data_purelib_folder: Path = self.__data_folder(WheelDataSubFolder.PURELIB)
        self.data_platlib_folder: Path = self.__data_folder(WheelDataSubFolder.PLATLIB)
        self.data_headers_folder: Path = self.__data_folder(WheelDataSubFolder.HEADERS)
        self.data_scripts_folder: Path = self.__data_folder(WheelDataSubFolder.SCRIPTS)
        self.data_data_folder: Path = self.__data_folder(WheelDataSubFolder.DATA)

    def __tag(self):
        impl = "py"
        major = sys.version_info.major
        minor = sys.version_info.minor
        python_tag = f"{impl}{major}{minor}"
        abi_tag = "none"
        platform_tag = sysconfig.get_platform().replace("-", "_").replace(".", "_")
        tag = f"{python_tag}-{abi_tag}-{platform_tag}"
        return tag

    def __archive_filename(self) -> Path:
        """Generate the wheel filename based on package name, version and platform tag."""
        return Path(f"{self.name}-{self.version}-{self.tag}.whl")

    def __dist_info_folder(self) -> Path:
        return self.path / Path(f"{self.name}-{self.version}.dist-info")
    
    def __data_folder(self, sub_folder: WheelDataSubFolder) -> Path:
        return self.path / Path(f"{self.name}-{self.version}.data") / sub_folder.value

class WheelBuilder:
    def __init__(self, path: Path, name: str, version: str):
        self.__path = path
        self.__temp = TemporaryDirectory(delete=True)
        self.__temp_path = Path(self.__temp.name)
        self.metadata = WheelMetadata(self.__temp_path, name, version)
        self.manifests = Manifests(self.metadata.dist_info_folder)

    @contextlib.contextmanager
    @staticmethod
    def extract(path: Path, package_name: str, package_version: str) -> Generator["WheelBuilder", None, None]:
        builder = WheelBuilder(path, package_name, package_version)
        builder.__extract()
        yield builder
        builder.__temp.cleanup()

    def __extract(self):
        safe_print_start(
            f"Extracting wheel package at {self.__temp_path}...", 
            printer=logger.info
        )
        with zipfile.ZipFile(self.__path, 'r') as zip_ref:
            zip_ref.extractall(self.__temp_path)
        safe_print_success(
            f"Wheel package extracted successfully.", 
            printer=logger.info
        )

    def build(self):
        safe_print_start(
            f"Building wheel package {self.metadata.archive_filename}...", 
            printer=logger.info
        )

        self.manifests.build()

        path = self.__path.parent / self.metadata.archive_filename;
        dist_info_folder_name = self.metadata.dist_info_folder.name
        
        # Create the wheel archive
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as wheel_zip:
            dist_info_files = []
            
            # Add all files from temp_path to the zip, except dist-info folder
            for file_path in self.__temp_path.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for the zip
                    relative_path = file_path.relative_to(self.__temp_path)
                    
                    # Skip dist-info folder files for now, we'll add them last
                    if str(relative_path.parent).endswith(dist_info_folder_name):
                        dist_info_files.append((file_path, relative_path))
                        safe_print_info(
                            f"File {relative_path} queued to wheel package.", 
                            printer=logger.info
                        )
                        continue
                    
                    wheel_zip.write(file_path, relative_path)

                    safe_print_info(
                        f"File {relative_path} added to wheel package.", 
                        printer=logger.info
                    )
            
            # Add dist-info folder files last for optimization
            for file_path, relative_path in dist_info_files:
                wheel_zip.write(file_path, relative_path)
                safe_print_info(
                    f"File {relative_path} added to wheel package.", 
                    printer=logger.info
                )

        safe_print_success(
            f"Wheel package {self.metadata.archive_filename} built successfully.", 
            printer=logger.info
        )
        
        