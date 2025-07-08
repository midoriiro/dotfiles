from contextlib import contextmanager
import logging
from pathlib import Path
import shutil
import tarfile
from typing import Any, Generator, Optional, override
from poexy_core.builders.builder import Builder

from poetry.core.poetry import Poetry
from poetry.core.masonry.utils.helpers import distribution_name

from poexy_core.manifest.manifest import PackageInfoManifest
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)

class SdistMetadata:
    def __init__(self, path: Path, name: str, version: str):
        self.path: Path = path
        self.name: str = distribution_name(name)
        self.version: str = version
        self.archive_path: Path = self.__archive_path()
        self.root_folder: Path = self.__root_folder()

    def __archive_path(self) -> Path:
        return self.path / Path(f"{self.name}-{self.version}.tar.gz")
    
    def __root_folder(self) -> Path:
        return self.path / Path(f"{self.name}-{self.version}")

class SdistBuilder(Builder):
    def __init__(
        self,
        poetry: Poetry,
        poexy: Poexy,
        format: PackageFormat,
        sdist_directory: Path | None = None,
        config_settings: dict[str, Any] | None = None,
    ):
        if format != PackageFormat.Source:
            raise ValueError(f"Invalid format: {format}")
        super().__init__(
            poetry,
            poexy,
            format,
            sdist_directory,
            config_settings
        )
        self.__metadata = SdistMetadata(
            self.temp_destination_directory,
            self.poetry.package.name,
            self.poetry.package.version.to_string(),
        )
        self.__manifest = PackageInfoManifest(self.__metadata.root_folder)

    def __add_files(self):
        pyproject_path = self.poetry.pyproject.path
        root_folder = self.__metadata.root_folder

        def add_file(source: Path, destination: Path):
            logger.info(f"Copying: {destination.relative_to(root_folder)}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, destination)

        add_file(pyproject_path, root_folder / "pyproject.toml")

        def predicate(_: Path) -> Optional[Path]:
            return root_folder

        self._add_files(
            predicate,
            add_file
        )

    @override
    @contextmanager
    def build(self) -> Generator[Path, None, None]:
        logger.info("Building sdist...")
        logger.info("Adding files...")
        self.__add_files()
        logger.info("Adding metadata...")
        self._add_metadata(self.__manifest)
        logger.info("Writing manifest...")
        self.__manifest.write()

        logger.info(f"Creating archive: {self.__metadata.archive_path.relative_to(self.__metadata.path)}")

        with tarfile.open(self.__metadata.archive_path, "w:gz", format=tarfile.GNU_FORMAT) as tar:
            queued_files = {}
            files = []
            
            def add_file(file: Path):
                relative_path = file.relative_to(self.__metadata.root_folder.parent)
                logger.info(f"Adding: {relative_path}")
                tar.add(file, arcname=relative_path)

            for file in self.__metadata.root_folder.rglob("*"):
                if file.is_dir():
                    continue
                relative_path = file.relative_to(self.__metadata.root_folder)
                if str(relative_path) == "pyproject.toml":
                    logger.info(f"Queuing: {relative_path}")
                    queued_files["pyproject.toml"] = file
                    continue
                if file.name == "PKG-INFO":
                    queued_files["PKG-INFO"] = file
                    logger.info(f"Queuing: {relative_path}")
                    continue
                files.append(file)

            for file in sorted(files):
                add_file(file)

            add_file(queued_files["pyproject.toml"])
            add_file(queued_files["PKG-INFO"])

        logger.info("Built successfully.")

        shutil.copy(self.__metadata.archive_path, self.destination_directory)

        yield self.__metadata.archive_path