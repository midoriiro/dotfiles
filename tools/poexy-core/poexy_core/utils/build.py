import logging
from pathlib import Path
from typing import List, Union

from poexy_core.utils import subprocess_rt
from poexy_core.utils.pip import UvOptions

logger = logging.getLogger(__name__)


class BuildError(Exception):
    pass


class BuildOptions(UvOptions):
    def __init__(self):
        super().__init__()
        self.__python_interpreter = None
        self.__sdist = None
        self.__wheel = None
        self.__output_path = None
        self.__force_pep517 = None
        self.__no_build_isolation = None

    @staticmethod
    def defaults() -> List[str]:
        default_options = UvOptions.defaults()
        options = BuildOptions()
        options.sdist(True)
        options.wheel(True)
        options.force_pep517(True)
        options.no_build_isolation(True)
        return default_options + options.build()

    def python_interpreter(self, python_interpreter: Path) -> "BuildOptions":
        self.__python_interpreter = python_interpreter
        return self

    def sdist(self, sdist: bool) -> "BuildOptions":
        self.__sdist = sdist
        return self

    def wheel(self, wheel: bool) -> "BuildOptions":
        self.__wheel = wheel
        return self

    def output_path(self, output_path: Path) -> "BuildOptions":
        self.__output_path = output_path
        return self

    def force_pep517(self, force_pep517: bool) -> "BuildOptions":
        self.__force_pep517 = force_pep517
        return self

    def no_build_isolation(self, no_build_isolation: bool) -> "BuildOptions":
        self.__no_build_isolation = no_build_isolation
        return self

    def build(self) -> List[str]:
        options = super().build()
        if self.__python_interpreter is not None:
            options.append("--python")
            options.append(str(self.__python_interpreter))
        if self.__sdist is not None and self.__sdist:
            options.append("--sdist")
        if self.__wheel is not None and self.__wheel:
            options.append("--wheel")
        if self.__output_path is not None:
            options.append("--out-dir")
            options.append(str(self.__output_path))
        if self.__force_pep517 is not None and self.__force_pep517:
            options.append("--force-pep517")
        if self.__no_build_isolation is not None and self.__no_build_isolation:
            options.append("--no-build-isolation")
        return options


class UvBuild:
    def __init__(self, binary_path: Path):
        self.__base_command = [str(binary_path), "build"]

    def build(self, source_path: Path, options: Union[BuildOptions, List[str]]) -> int:
        if isinstance(options, BuildOptions):
            options = options.build()
        elif not isinstance(options, list):
            raise BuildError(
                f"Invalid arguments type: {type(options)}. "
                f"Expected: {type(BuildOptions)} or {type(List[str])}"
            )
        cmd = [*self.__base_command, *options, str(source_path)]
        exit_code = subprocess_rt.run(cmd, printer=logger.info)
        if exit_code != 0:
            raise BuildError(f"Failed to build: {cmd}")
        return exit_code
