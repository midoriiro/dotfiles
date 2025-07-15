import logging
import shutil
import tarfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional, override

from packaging.utils import NormalizedName
from poetry.core.masonry.utils.helpers import distribution_name
from poetry.core.poetry import Poetry

from poexy_core.builders.builder import Builder
from poexy_core.builders.hooks.include_files import IncludeFilesHookBuilder
from poexy_core.builders.hooks.license import LicenseHookBuilder
from poexy_core.builders.hooks.package_files import PackageFilesHookBuilder
from poexy_core.builders.hooks.readme import ReadmeHookBuilder
from poexy_core.manifest.manifest import PackageInfoManifest
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)


class SdistMetadata:
    def __init__(self, path: Path, name: str, version: str):
        self.path: Path = path
        self.name: str = distribution_name(NormalizedName(name))
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
        _format: PackageFormat,
        sdist_directory: Path,
        config_settings: dict[str, Any] | None = None,
    ):
        if _format != PackageFormat.Source:
            raise ValueError(f"Invalid format: {_format}")
        super().__init__(poetry, poexy, _format, sdist_directory, config_settings)
        self.__metadata = SdistMetadata(
            self.temp_destination_directory,
            self.poetry.package.name,
            self.poetry.package.version.to_string(),
        )
        self.__manifest = PackageInfoManifest(self.__metadata.root_folder)
        self.__archive: Optional[tarfile.TarFile] = None

        self._hooks.append(
            ReadmeHookBuilder(self.poetry, self.poexy, self.__metadata.root_folder)
        )
        self._hooks.append(
            PackageFilesHookBuilder(
                self.poexy, self.format, lambda path: self.__metadata.root_folder
            )
        )
        self._hooks.append(
            IncludeFilesHookBuilder(
                self.poexy, self.format, self.__metadata.root_folder
            )
        )
        self._hooks.append(LicenseHookBuilder(self.poexy, self.__metadata.root_folder))

    def __add_files(self):
        for hook in self._hooks:
            hook.add_files(self.__add_files_to_archive)

    @contextmanager
    def __create_archive(self) -> Generator[None, None, None]:
        logger.info(
            "Creating archive: "
            f"{self.__metadata.archive_path.relative_to(self.__metadata.path)}"
        )
        self.__archive = tarfile.open(
            self.__metadata.archive_path, "w:gz", format=tarfile.GNU_FORMAT
        )
        yield
        self.__archive.close()
        self.__archive = None

    def __add_files_to_archive(self, source: Path, destination: Path):
        if self.__archive is None:
            raise ValueError("Archive not created")
        relative_path = destination.relative_to(self.__metadata.root_folder.parent)
        logger.info(f"Adding: {relative_path}")
        self.__archive.add(source, arcname=relative_path)

    def __add_pkginfo_and_pyproject_to_archive(self):
        if self.__archive is None:
            raise ValueError("Archive not created")
        pyproject_path = self.poetry.pyproject.path
        self.__add_files_to_archive(
            pyproject_path,
            self.__metadata.root_folder / pyproject_path.name,
        )
        self.__add_files_to_archive(
            self.__manifest.path,
            self.__metadata.root_folder / self.__manifest.path.name,
        )

    @override
    @contextmanager
    def build(self) -> Generator[Path, None, None]:
        logger.info("Building sdist...")

        for hook in self._hooks:
            hook.build()

        with self.__create_archive():
            logger.info("Adding metadata...")
            self._add_metadata(self.__manifest)
            logger.info("Writing manifest...")
            self.__manifest.write()
            logger.info("Adding files...")
            self.__add_files()
            logger.info("Adding pkginfo and pyproject files...")
            self.__add_pkginfo_and_pyproject_to_archive()

        logger.info("Built successfully.")

        shutil.copy(self.__metadata.archive_path, self.destination_directory)

        yield self.__metadata.archive_path
