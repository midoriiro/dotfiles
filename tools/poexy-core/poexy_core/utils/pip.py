from enum import Enum
from pathlib import Path
from typing import List, Union, override

from poexy_core.utils import subprocess_rt


class UvLinkMode(Enum):
    Clone = "clone"
    Copy = "copy"
    Hardlink = "hardlink"
    Symlink = "symlink"


class PipError(Exception):
    pass


class PackageInstallerProgramOptions:
    @staticmethod
    def defaults() -> List[str]:
        raise NotImplementedError

    def build(self) -> List[str]:
        raise NotImplementedError


class UvOptions(PackageInstallerProgramOptions):
    def __init__(self):
        self.__verbose = None
        self.__offline = None
        self.__no_config = None
        self.__cache_dir = None

    @staticmethod
    @override
    def defaults() -> List[str]:
        options = UvOptions()
        options.verbose(True)
        options.no_config(True)
        return options.build()

    def verbose(self, verbose: bool) -> "UvOptions":
        self.__verbose = verbose
        return self

    def offline(self, offline: bool) -> "UvOptions":
        self.__offline = offline
        return self

    def no_config(self, no_config: bool) -> "UvOptions":
        self.__no_config = no_config
        return self

    def cache_dir(self, cache_dir: Path) -> "UvOptions":
        self.__cache_dir = cache_dir
        return self

    @override
    def build(self) -> List[str]:
        options = []
        if self.__verbose is not None and self.__verbose:
            options.append("--verbose")
        if self.__offline is not None and self.__offline:
            options.append("--offline")
        if self.__no_config is not None and self.__no_config:
            options.append("--no-config")
        if self.__cache_dir is not None:
            options.append("--cache-dir")
            options.append(str(self.__cache_dir))
        return options


class UvInstallOptions(UvOptions):
    def __init__(self):
        super().__init__()
        self.__python_interpreter = None
        self.__prefix = None
        self.__strict = None
        self.__dry_run = None
        self.__link_mode = None
        self.__reinstall = None
        self.__no_build_isolation = None

    @staticmethod
    @override
    def defaults() -> List[str]:
        options = UvInstallOptions()
        options.link_mode(UvLinkMode.Symlink)
        options.reinstall(True)
        return UvOptions.defaults() + options.build()

    def python_interpreter(self, python_interpreter: Path) -> "UvInstallOptions":
        self.__python_interpreter = python_interpreter
        return self

    def prefix(self, prefix: Path) -> "UvInstallOptions":
        self.__prefix = prefix
        return self

    def strict(self, strict: bool) -> "UvInstallOptions":
        self.__strict = strict
        return self

    def dry_run(self, dry_run: bool) -> "UvInstallOptions":
        self.__dry_run = dry_run
        return self

    def link_mode(self, link_mode: UvLinkMode) -> "UvInstallOptions":
        self.__link_mode = link_mode
        return self

    def reinstall(self, reinstall: bool) -> "UvInstallOptions":
        self.__reinstall = reinstall
        return self

    def no_build_isolation(self, no_build_isolation: bool) -> "UvInstallOptions":
        self.__no_build_isolation = no_build_isolation
        return self

    @override
    def build(self) -> List[str]:
        options = super().build()
        if self.__python_interpreter is not None:
            options.append("--python")
            options.append(str(self.__python_interpreter))
        if self.__prefix is not None:
            options.append("--prefix")
            options.append(str(self.__prefix))
        if self.__strict is not None and self.__strict:
            options.append("--strict")
        if self.__dry_run is not None and self.__dry_run:
            options.append("--dry-run")
        if self.__link_mode is not None:
            options.append("--link-mode")
            options.append(self.__link_mode.value)
        if self.__reinstall is not None and self.__reinstall:
            options.append("--reinstall")
        if self.__no_build_isolation is not None and self.__no_build_isolation:
            options.append("--no-build-isolation")
        return options


class PipOptions(PackageInstallerProgramOptions):
    def __init__(self):
        self.__verbose = None
        self.__debug = None
        self.__require_virtualenv = None
        self.__isolated = None
        self.__cache_dir = None

    @staticmethod
    @override
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

    @override
    def build(self) -> List[str]:
        options = []
        if self.__verbose is not None and self.__verbose:
            options.append("--verbose")
        if self.__debug is not None and self.__debug:
            options.append("--debug")
        if self.__require_virtualenv is not None and self.__require_virtualenv:
            options.append("--require-virtualenv")
        if self.__isolated is not None and self.__isolated:
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
    @override
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

    @override
    def build(self) -> List[str]:
        options = super().build()
        if self.__prefix is not None:
            options.append("--prefix")
            options.append(str(self.__prefix))
        if self.__use_pep517 is not None and self.__use_pep517:
            options.append("--use-pep517")
        if self.__no_build_isolation is not None and self.__no_build_isolation:
            options.append("--no-build-isolation")
        if (
            self.__check_build_dependencies is not None
            and self.__check_build_dependencies
        ):
            options.append("--check-build-dependencies")
        if self.__no_clean is not None and self.__no_clean:
            options.append("--no-clean")
        if self.__force_reinstall is not None and self.__force_reinstall:
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

    @override
    def build(self) -> List[str]:
        options = super().build()
        if self.__wheel_dir is not None:
            options.append("--wheel-dir")
            options.append(str(self.__wheel_dir))
        if self.__no_build_isolation is not None and self.__no_build_isolation:
            options.append("--no-build-isolation")
        if (
            self.__check_build_dependencies is not None
            and self.__check_build_dependencies
        ):
            options.append("--check-build-dependencies")
        if self.__no_clean is not None and self.__no_clean:
            options.append("--no-clean")
        return options


class PackageInstallerProgram:
    def __init__(self, binary_path: Path):
        self._binary_path = binary_path

    def _execute_command(self, arguments: List[str]) -> int:
        cmd = [str(self._binary_path), *arguments]
        exit_code = subprocess_rt.run(cmd, printer=print)
        if exit_code != 0:
            raise PipError(f"Failed to execute {self._binary_path.name} command: {cmd}")
        return exit_code

    def install(
        self,
        packages: List[str],
        arguments: Union[PackageInstallerProgramOptions, List[str]],
    ) -> int:
        raise NotImplementedError

    def wheel(
        self,
        packages: List[str],
        arguments: Union[PackageInstallerProgramOptions, List[str]],
    ) -> int:
        raise NotImplementedError

    def show(
        self, package: str, arguments: Union[PackageInstallerProgramOptions, List[str]]
    ) -> int:
        raise NotImplementedError


class Pip(PackageInstallerProgram):
    @override
    def install(
        self,
        packages: List[str],
        arguments: Union[PackageInstallerProgramOptions, List[str]],
    ) -> int:
        if isinstance(arguments, PipInstallOptions):
            arguments = arguments.build()
        elif not isinstance(arguments, list):
            raise PipError(
                f"Invalid arguments type: {type(arguments)}. "
                f"Expected: {type(PipInstallOptions)} or {type(List[str])}"
            )
        return self._execute_command(["install", *arguments, *packages])

    @override
    def wheel(
        self,
        packages: List[str],
        arguments: Union[PackageInstallerProgramOptions, List[str]],
    ) -> int:
        if isinstance(arguments, PipWheelOptions):
            arguments = arguments.build()
        elif not isinstance(arguments, list):
            raise PipError(
                f"Invalid arguments type: {type(arguments)}. "
                f"Expected: {type(PipWheelOptions)} or {type(List[str])}"
            )
        return self._execute_command(["wheel", *arguments, *packages])

    @override
    def show(
        self, package: str, arguments: Union[PackageInstallerProgramOptions, List[str]]
    ) -> int:
        if isinstance(arguments, PipOptions):
            arguments = arguments.build()
        elif not isinstance(arguments, list):
            raise PipError(
                f"Invalid arguments type: {type(arguments)}. "
                f"Expected: {type(PipOptions)} or {type(List[str])}"
            )
        return self._execute_command(["show", *arguments, package])


class Uv(PackageInstallerProgram):
    def __init__(
        self, python_path: Path, binary_path: Path, fallback: PackageInstallerProgram
    ):
        super().__init__(binary_path)
        self.__python_path = python_path
        self.__fallback = fallback

        if not self._binary_path.exists():
            self.__fallback.install(["uv"], PipInstallOptions.defaults())

    @override
    def install(
        self,
        packages: List[str],
        arguments: Union[PackageInstallerProgramOptions, List[str]],
    ) -> int:
        if isinstance(arguments, UvInstallOptions):
            arguments.python_interpreter(self.__python_path)
            arguments = arguments.build()
        elif isinstance(arguments, list):
            install_options = UvInstallOptions()
            install_options.python_interpreter(self.__python_path)
            arguments = install_options.build() + arguments
        elif not isinstance(arguments, list):
            raise PipError(
                f"Invalid arguments type: {type(arguments)}. "
                f"Expected: {type(UvInstallOptions)} or {type(List[str])}"
            )
        packages_to_install_with_fallback = []
        for index, package in enumerate(reversed(packages)):
            if "@ git+git://" in package:
                packages_to_install_with_fallback.append(package)
                packages.pop(index)
        if len(packages_to_install_with_fallback) > 0:
            self.__fallback.install(
                packages_to_install_with_fallback, PipInstallOptions.defaults()
            )
        if len(packages) == 0:
            return 0
        return self._execute_command(["pip", "install", *arguments, *packages])

    @override
    def wheel(
        self,
        packages: List[str],
        arguments: Union[PackageInstallerProgramOptions, List[str]],
    ) -> int:
        if isinstance(arguments, PipWheelOptions):
            arguments = arguments.build()
        elif not isinstance(arguments, list):
            raise PipError(
                f"Invalid arguments type: {type(arguments)}. "
                f"Expected: {type(PipWheelOptions)} or {type(List[str])}"
            )
        return self.__fallback.wheel(packages, arguments)

    @override
    def show(
        self, package: str, arguments: Union[PackageInstallerProgramOptions, List[str]]
    ) -> int:
        if isinstance(arguments, UvOptions):
            arguments = arguments.build()
        elif not isinstance(arguments, list):
            raise PipError(
                f"Invalid arguments type: {type(arguments)}. "
                f"Expected: {type(UvOptions)} or {type(List[str])}"
            )
        return self._execute_command(["pip", "show", *arguments, package])
