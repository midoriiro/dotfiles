import logging
from pathlib import Path
from typing import List, Union, override

from poexy_core.utils import subprocess_rt
from poexy_core.utils.pip.options import (
    PackageInstallerProgramOptions,
    PipInstallOptions,
    PipOptions,
    PipWheelOptions,
    UvInstallOptions,
    UvOptions,
)

logger = logging.getLogger(__name__)


class PipError(Exception):
    pass


class PackageInstallerProgram:
    def __init__(self, binary_path: Path):
        self._binary_path = binary_path

    def _execute_command(self, arguments: List[str]) -> int:
        logs = []

        def log_command(line: str):
            logger.info(line)
            logs.append(line)

        cmd = [str(self._binary_path), *arguments]
        exit_code = subprocess_rt.run(cmd, printer=log_command)
        if exit_code != 0:
            raise PipError(
                f"Failed to execute {self._binary_path.name}: \n"
                f"Command: {cmd}\n"
                f"Logs: \n{"\n".join(logs)}"
            )
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
