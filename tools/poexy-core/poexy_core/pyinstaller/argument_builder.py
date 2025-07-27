import logging
from pathlib import Path
from typing import List

from poexy_core.pyinstaller.types import BuildType

logger = logging.getLogger(__name__)


class PyInstallerArgumentBuilderError(Exception):
    pass


class PyInstallerArgumentBuilder:
    def __init__(self) -> None:
        self.__executable_name = None
        self.__build_type = None
        self.__entry_point = None
        self.__spec_path = None
        self.__dist_path = None
        self.__work_path = None
        self.__collect_submodules = None
        self.__paths = None
        self.__strip = None
        self.__clean = None

    def executable_name(self, executable_name: str) -> "PyInstallerArgumentBuilder":
        self.__executable_name = executable_name
        return self

    def build_type(self, build_type: BuildType) -> "PyInstallerArgumentBuilder":
        self.__build_type = build_type
        return self

    def entry_point(self, entry_point: Path) -> "PyInstallerArgumentBuilder":
        self.__entry_point = entry_point
        return self

    def spec_path(self, spec_path: Path) -> "PyInstallerArgumentBuilder":
        self.__spec_path = spec_path
        return self

    def dist_path(self, dist_path: Path) -> "PyInstallerArgumentBuilder":
        self.__dist_path = dist_path
        return self

    def work_path(self, work_path: Path) -> "PyInstallerArgumentBuilder":
        self.__work_path = work_path
        return self

    def collect_submodules(
        self, submodules: List[Path]
    ) -> "PyInstallerArgumentBuilder":
        if len(submodules) == 0:
            raise PyInstallerArgumentBuilderError("Submodules cannot be empty")
        self.__collect_submodules = submodules
        return self

    def paths(self, paths: List[Path]) -> "PyInstallerArgumentBuilder":
        if len(paths) == 0:
            raise PyInstallerArgumentBuilderError("Paths cannot be empty")
        self.__paths = paths
        return self

    def strip(self, strip: bool) -> "PyInstallerArgumentBuilder":
        self.__strip = strip
        return self

    def clean(self, clean: bool) -> "PyInstallerArgumentBuilder":
        self.__clean = clean
        return self

    def build(self) -> List[str]:
        arguments = []

        logger.info("Building executable with arguments:")

        if self.__entry_point is not None:
            logger.info(f"  - Entry point: {self.__entry_point}")
            arguments.append(str(self.__entry_point))

        if self.__executable_name is not None:
            logger.info(f"  - Executable name: {self.__executable_name}")
            arguments.append("--name")
            arguments.append(self.__executable_name)

        if self.__build_type is not None:
            logger.info(f"  - Build type: {self.__build_type}")
            arguments.append(f"--{self.__build_type.value}")

        if self.__spec_path is not None:
            logger.info(f"  - Spec path: {self.__spec_path}")
            arguments.append("--specpath")
            arguments.append(str(self.__spec_path))

        if self.__dist_path is not None:
            logger.info(f"  - Dist path: {self.__dist_path}")
            arguments.append("--distpath")
            arguments.append(str(self.__dist_path))

        if self.__work_path is not None:
            logger.info(f"  - Work path: {self.__work_path}")
            arguments.append("--workpath")
            arguments.append(str(self.__work_path))

        if self.__collect_submodules is not None:
            for submodule in self.__collect_submodules:
                logger.info(f"  - Collect submodule: {submodule}")
                arguments.append("--collect-submodules")
                arguments.append(str(submodule))

        if self.__paths is not None:
            for path in self.__paths:
                logger.info(f"  - Path: {path}")
                arguments.append("--paths")
                arguments.append(str(path))

        if self.__strip is not None:
            logger.info(f"  - Strip: {self.__strip}")
            arguments.append("--strip")

        if self.__clean is not None:
            logger.info(f"  - Clean: {self.__clean}")
            arguments.append("--clean")

        return arguments
