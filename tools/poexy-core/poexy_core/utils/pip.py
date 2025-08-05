from pathlib import Path
from typing import List, Union

from poexy_core.utils import subprocess_rt


class PipError(Exception):
    pass


class PipOptions:
    def __init__(self):
        self.__verbose = None
        self.__debug = None
        self.__require_virtualenv = None
        self.__isolated = None
        self.__cache_dir = None

    @staticmethod
    def defaults() -> List[str]:
        options = PipOptions()
        options.verbose(True)
        options.require_virtualenv(True)
        options.isolated(True)
        return options.build()

    def verbose(self, verbose: bool) -> "PipOptions":
        self.__verbose = verbose
        return self

    def debug(self, debug: bool) -> "PipOptions":
        self.__debug = debug
        return self

    def require_virtualenv(self, require_virtualenv: bool) -> "PipOptions":
        self.__require_virtualenv = require_virtualenv
        return self

    def isolated(self, isolated: bool) -> "PipOptions":
        self.__isolated = isolated
        return self

    def cache_dir(self, cache_dir: Path) -> "PipOptions":
        self.__cache_dir = cache_dir
        return self

    def build(self) -> List[str]:
        options = []
        if self.__verbose is not None:
            options.append("--verbose")
        if self.__debug is not None:
            options.append("--debug")
        if self.__require_virtualenv is not None:
            options.append("--require-virtualenv")
        if self.__isolated is not None:
            options.append("--isolated")
        if self.__cache_dir is not None:
            options.append("--cache-dir")
            options.append(str(self.__cache_dir))
        return options


class PipInstallOptions(PipOptions):
    def __init__(self):
        super().__init__()
        self.__prefix = None
        self.__use_pep517 = None
        self.__no_build_isolation = None
        self.__check_build_dependencies = None
        self.__no_clean = None
        self.__force_reinstall = None

    @staticmethod
    def defaults() -> List[str]:
        options = PipInstallOptions()
        options.use_pep517(True)
        options.no_build_isolation(True)
        options.check_build_dependencies(True)
        return PipOptions.defaults() + options.build()

    def prefix(self, prefix: Path) -> "PipInstallOptions":
        self.__prefix = prefix
        return self

    def use_pep517(self, use_pep517: bool) -> "PipInstallOptions":
        self.__use_pep517 = use_pep517
        return self

    def no_build_isolation(self, no_build_isolation: bool) -> "PipInstallOptions":
        self.__no_build_isolation = no_build_isolation
        return self

    def check_build_dependencies(
        self, check_build_dependencies: bool
    ) -> "PipInstallOptions":
        self.__check_build_dependencies = check_build_dependencies
        return self

    def no_clean(self, no_clean: bool) -> "PipInstallOptions":
        self.__no_clean = no_clean
        return self

    def force_reinstall(self, force_reinstall: bool) -> "PipInstallOptions":
        self.__force_reinstall = force_reinstall
        return self

    def build(self) -> List[str]:
        options = super().build()
        if self.__prefix is not None:
            options.append("--prefix")
            options.append(str(self.__prefix))
        if self.__use_pep517 is not None:
            options.append("--use-pep517")
        if self.__no_build_isolation is not None:
            options.append("--no-build-isolation")
        if self.__check_build_dependencies is not None:
            options.append("--check-build-dependencies")
        if self.__no_clean is not None:
            options.append("--no-clean")
        if self.__force_reinstall is not None:
            options.append("--force-reinstall")
        return options


class PipWheelOptions(PipOptions):
    def __init__(self):
        super().__init__()
        self.__wheel_dir = None
        self.__no_build_isolation = None
        self.__check_build_dependencies = None
        self.__no_clean = None

    def wheel_dir(self, wheel_dir: Path) -> "PipWheelOptions":
        self.__wheel_dir = wheel_dir
        return self

    def no_build_isolation(self, no_build_isolation: bool) -> "PipWheelOptions":
        self.__no_build_isolation = no_build_isolation
        return self

    def check_build_dependencies(
        self, check_build_dependencies: bool
    ) -> "PipWheelOptions":
        self.__check_build_dependencies = check_build_dependencies
        return self

    def no_clean(self, no_clean: bool) -> "PipWheelOptions":
        self.__no_clean = no_clean
        return self

    def build(self) -> List[str]:
        options = super().build()
        if self.__wheel_dir is not None:
            options.append("--wheel-dir")
            options.append(str(self.__wheel_dir))
        if self.__no_build_isolation is not None:
            options.append("--no-build-isolation")
        if self.__check_build_dependencies is not None:
            options.append("--check-build-dependencies")
        if self.__no_clean is not None:
            options.append("--no-clean")
        return options


class Pip:
    def __init__(self, binary_path: Path):
        self.__binary_path = binary_path

    def __execute_pip_command(self, arguments: List[str]) -> int:
        cmd = [str(self.__binary_path), *arguments]
        exit_code = subprocess_rt.run(cmd, printer=print)
        if exit_code != 0:
            raise PipError(f"Failed to execute pip command: {cmd}")
        return exit_code

    def install(
        self, packages: List[str], arguments: Union[PipInstallOptions, List[str]]
    ) -> int:
        if isinstance(arguments, PipInstallOptions):
            arguments = arguments.build()
        return self.__execute_pip_command(["install", *arguments, *packages])

    def wheel(
        self, packages: List[str], arguments: Union[PipWheelOptions, List[str]]
    ) -> int:
        if isinstance(arguments, PipWheelOptions):
            arguments = arguments.build()
        return self.__execute_pip_command(["wheel", *arguments, *packages])

    def show(self, package: str, arguments: Union[PipOptions, List[str]]) -> int:
        if isinstance(arguments, PipOptions):
            arguments = arguments.build()
        return self.__execute_pip_command(["show", *arguments, package])
