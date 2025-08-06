import logging
from pathlib import Path
from typing import List, Union

from poexy_core.utils import subprocess_rt

logger = logging.getLogger(__name__)


class BuildError(Exception):
    pass


class BuildOptions:
    def __init__(self):
        self.__verbose = None
        self.__sdist = None
        self.__wheel = None
        self.__output_path = None
        self.__no_isolation = None

    @staticmethod
    def defaults() -> List[str]:
        options = BuildOptions()
        options.verbose(True)
        options.sdist(True)
        options.wheel(True)
        return options.build()

    def verbose(self, verbose: bool) -> "BuildOptions":
        self.__verbose = verbose
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

    def no_isolation(self, no_isolation: bool) -> "BuildOptions":
        self.__no_isolation = no_isolation
        return self

    def build(self) -> List[str]:
        options = []
        if self.__verbose is not None:
            options.append("--verbose")
        if self.__sdist is not None and self.__sdist:
            options.append("--sdist")
        if self.__wheel is not None and self.__wheel:
            options.append("--wheel")
        if self.__output_path is not None:
            options.append("--outdir")
            options.append(str(self.__output_path))
        if self.__no_isolation is not None and self.__no_isolation:
            options.append("--no-isolation")
        return options


class Build:
    def __init__(self, binary_path: Path):
        self.__base_command = [str(binary_path), "-m", "build"]

    def build(self, source_path: Path, options: Union[BuildOptions, List[str]]) -> int:
        if isinstance(options, BuildOptions):
            options = options.build()
        cmd = [*self.__base_command, *options, str(source_path)]
        exit_code = subprocess_rt.run(cmd, printer=logger.info)
        if exit_code != 0:
            raise BuildError(f"Failed to build: {cmd}")
        return exit_code
