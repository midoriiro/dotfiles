import ast
import logging
from pathlib import Path
from typing import Optional

from poetry.core.poetry import Poetry

from poexy_core.packages.format import WheelFormat
from poexy_core.pyinstaller.argument_builder import PyInstallerArgumentBuilder
from poexy_core.pyinstaller.types import BuildType
from poexy_core.pyinstaller.venv import PyinstallerVirtualEnvironment
from poexy_core.pyproject.tables.poexy import Poexy
from poexy_core.pyproject.toml import PyProjectTOML
from poexy_core.utils import subprocess_rt

logger = logging.getLogger(__name__)


class PyinstallerBuilderError(Exception):
    pass


class PyinstallerBuilder:
    def __init__(self, poetry: Poetry, poexy: Poexy):
        self.__project_path = poetry.pyproject_path.parent
        if poexy.package.source is None:
            raise PyinstallerBuilderError(
                "Package source is not defined in pyproject.toml at "
                "[tool.poexy.package.${package_name}.source]"
            )
        self.__package_source_path = poexy.package.source
        wheel = poexy.wheel
        if wheel is not None and WheelFormat.Binary not in wheel.format:
            raise PyinstallerBuilderError(
                "Cannot build binary executable for wheel package as specified in "
                "[tool.poexy.wheel.format]"
            )
        binary = poexy.binary
        if binary is None:
            raise PyinstallerBuilderError(
                "Binary package is not defined in pyproject.toml at [tool.poexy.binary]"
            )
        if binary.name is None:
            raise PyinstallerBuilderError(
                "Binary package name is not defined in pyproject.toml at "
                "[tool.poexy.binary.name]"
            )
        self.__executable_name = binary.name
        self.__entry_point = binary.entry_point
        self.__dependencies = PyProjectTOML.dependencies_from_poetry(poetry)

    @property
    def executable_name(self) -> str:
        return self.__executable_name

    @staticmethod
    def __has_main_block(path: Path) -> bool:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "__name__"
                    and len(test.ops) == 1
                    and isinstance(test.ops[0], ast.Eq)
                    and len(test.comparators) == 1
                    and isinstance(test.comparators[0], ast.Constant)
                    and test.comparators[0].value == "__main__"
                ):
                    return True
        return False

    @staticmethod
    def __find_entry_point(base_path: Path) -> str:
        for file in base_path.rglob("**/*.py"):
            if not file.is_file():
                continue
            if PyinstallerBuilder.__has_main_block(file):
                return str(file)
        raise PyinstallerBuilderError("No entry point found")

    def __build(self, arguments: PyInstallerArgumentBuilder) -> None:
        command = ["pyinstaller", *arguments.build()]
        exit_code = subprocess_rt.run(
            command, printer=logger.info, cwd=self.__project_path
        )
        if exit_code != 0:
            raise PyinstallerBuilderError("Failed to build executable")

    def __build_with_venv(self, arguments: PyInstallerArgumentBuilder) -> None:
        with PyinstallerVirtualEnvironment.create() as venv:
            directory_dependencies = venv.install_dependencies(self.__dependencies)
            for directory_dependency in directory_dependencies:
                arguments.paths([directory_dependency.full_path])
            self.__build(arguments)

    def build(
        self,
        build_type: Optional[BuildType] = BuildType.OneFile,
        build_path: Optional[Path] = None,
        dist_path: Optional[Path] = None,
        strip: Optional[bool] = True,
        clean: Optional[bool] = True,
    ):
        if self.__entry_point is None:
            self.__entry_point = PyinstallerBuilder.__find_entry_point(
                self.__package_source_path
            )
        path_to_entry_point = Path(self.__project_path) / self.__entry_point
        if not path_to_entry_point.is_file():
            raise PyinstallerBuilderError(
                f"Entry point {self.__entry_point} is not a file"
            )
        if not path_to_entry_point.exists():
            raise PyinstallerBuilderError(
                f"Entry point {self.__entry_point} does not exist"
            )
        spec_path = str(build_path or self.__project_path / "build" / "spec")
        if dist_path is None:
            dist_path = self.__project_path / "dist"
        work_path = str(build_path or self.__project_path / "build" / "temp")

        collect_submodules = self.__package_source_path.resolve()

        arguments = PyInstallerArgumentBuilder()
        arguments.executable_name(self.__executable_name)
        arguments.build_type(build_type)
        arguments.entry_point(path_to_entry_point)
        arguments.spec_path(spec_path)
        arguments.dist_path(dist_path)
        arguments.work_path(work_path)
        arguments.collect_submodules([collect_submodules])

        if strip is not None:
            arguments.strip(strip)
        if clean is not None:
            arguments.clean(clean)

        if len(self.__dependencies) > 0:
            self.__build_with_venv(arguments)
        else:
            self.__build(arguments)

        logger.info("Executable built successfully.")
