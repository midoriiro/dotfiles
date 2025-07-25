import logging
from pathlib import Path
from typing import Any

from rich.console import Console

from poexy_core.builders.binary import BinaryBuilder
from poexy_core.builders.hooks.binary import BinaryHookBuilder
from poexy_core.builders.sdist import SdistBuilder
from poexy_core.builders.wheel import WheelBuilder
from poexy_core.packages.format import PackageFormat, WheelFormat
from poexy_core.pyproject.toml import PyProjectTOML

# pylint: disable=no-member

console = Console()


class ConsoleHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            print(msg)
        except Exception:
            self.handleError(record)


console_handler = ConsoleHandler()
console_handler.setFormatter(logging.Formatter("%(message)s"))

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure root logger to show all logs
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Also configure poexy_core logger
poexy_logger = logging.getLogger("poexy_core")
poexy_logger.setLevel(logging.INFO)
poexy_logger.addHandler(console_handler)


class PoexyBuilderError(Exception):
    pass


def __get_wheel_builder(
    wheel_directory: str | None = None,
    metadata_directory: str | None = None,
    config_settings: dict[str, Any] | None = None,
) -> WheelBuilder:
    pyproject = PyProjectTOML(path=Path.cwd())
    poexy = pyproject.poexy
    poetry = pyproject.poetry
    if metadata_directory is not None:
        destination_directory = metadata_directory
    elif wheel_directory is not None:
        destination_directory = wheel_directory
    else:
        raise ValueError("wheel_directory and metadata_directory cannot be None")
    metadata_path = None if metadata_directory is None else Path(metadata_directory)
    wheel_builder = WheelBuilder(
        poetry,
        poexy,
        PackageFormat.Wheel,
        wheel_directory=Path(destination_directory),
        metadata_directory=metadata_path,
        config_settings=config_settings,
    )
    if poexy.wheel is None:
        raise PoexyBuilderError(
            "Wheel package is not defined in pyproject.toml at [tool.poexy.wheel]"
        )
    binary_builder = __get_binary_builder(
        wheel_directory=wheel_directory,
        metadata_directory=metadata_directory,
        config_settings=config_settings,
    )
    if poexy.wheel.format is not None:
        wheel_format = list(poexy.wheel.format)
        if len(wheel_format) > 1 and WheelFormat.Binary in wheel_format:
            wheel_builder.add_hook(BinaryHookBuilder(binary_builder))
            return wheel_builder
        if len(wheel_format) == 1 and WheelFormat.Binary not in wheel_format:
            return wheel_builder
        if len(wheel_format) == 1 and WheelFormat.Binary in wheel_format:
            return binary_builder
        raise PoexyBuilderError("Wheel package format is not valid")
    raise PoexyBuilderError(
        "Wheel package format is not defined in pyproject.toml at "
        "[tool.poexy.wheel] or [tool.poexy.binary]"
    )


def __get_binary_builder(
    wheel_directory: str | None = None,
    metadata_directory: str | None = None,
    config_settings: dict[str, Any] | None = None,
) -> BinaryBuilder:
    pyproject = PyProjectTOML(path=Path.cwd())
    poexy = pyproject.poexy
    poetry = pyproject.poetry
    if metadata_directory is not None:
        destination_directory = metadata_directory
    elif wheel_directory is not None:
        destination_directory = wheel_directory
    else:
        raise ValueError("wheel_directory and metadata_directory cannot be None")
    metadata_path = None if metadata_directory is None else Path(metadata_directory)
    builder = BinaryBuilder(
        poetry,
        poexy,
        PackageFormat.Binary,
        wheel_directory=Path(destination_directory),
        metadata_directory=metadata_path,
        config_settings=config_settings,
    )
    return builder


def __get_sdist_builder(
    sdist_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> SdistBuilder:
    pyproject = PyProjectTOML(path=Path.cwd())
    poexy = pyproject.poexy
    poetry = pyproject.poetry
    builder = SdistBuilder(
        poetry,
        poexy,
        PackageFormat.Source,
        sdist_directory=Path(sdist_directory),
        config_settings=config_settings,
    )
    return builder


def get_requires_for_build_wheel(
    config_settings: dict[str, Any] | None = None,
) -> list[str]:
    """
    Returns an additional list of requirements for building, as PEP508 strings,
    above and beyond those specified in the pyproject.toml file.

    This implementation is optional. At the moment it only returns an empty list,
    which would be the same as if not define. So this is just for completeness
    for future implementation.
    """

    logger.info("=== Get requires for build wheel called ===")
    logger.info(f"config_settings: {config_settings}")

    try:
        pyproject = PyProjectTOML(path=Path().resolve())
        logger.info("Pyproject loaded successfully")
        required_packages = pyproject.build_system.requires
        logger.info(f"Required packages: {required_packages}")
        return required_packages
    except Exception as e:
        logger.error(f"Error in get_requires_for_build_wheel: {e}")
        raise


# For now, we require all dependencies to build either a wheel or an sdist.
get_requires_for_build_sdist = get_requires_for_build_wheel


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: dict[str, Any] | None = None
) -> str:
    logger.info("=== Prepare metadata for build wheel called ===")
    logger.info(f"metadata_directory: {metadata_directory}")
    logger.info(f"config_settings: {config_settings}")

    try:
        builder = __get_wheel_builder(
            metadata_directory=metadata_directory, config_settings=config_settings
        )
        logger.info("Builder created successfully")
        dist_info = builder.prepare()
        logger.info(f"Metadata prepared, dist_info: {dist_info}")
        logger.info(f"Returning dist_info.name: {dist_info.name}")
        return dist_info.name
    except Exception as e:
        logger.error(f"Error in prepare_metadata_for_build_wheel: {e}")
        raise


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Builds a wheel, places it in wheel_directory"""
    logger.info("=== Build wheel called ===")
    logger.info(f"wheel_directory: {wheel_directory}")
    logger.info(f"config_settings: {config_settings}")
    logger.info(f"metadata_directory: {metadata_directory}")

    try:
        builder = __get_wheel_builder(
            wheel_directory=wheel_directory, config_settings=config_settings
        )
        logger.info("Builder created successfully")
        with builder.build() as file_path:
            logger.info(f"Wheel built successfully, file_path: {file_path}")
            return file_path.name
    except Exception as e:
        logger.error(f"Error in build_wheel: {e}")
        raise


def build_sdist(
    sdist_directory: str, config_settings: dict[str, Any] | None = None
) -> str:
    """Builds an sdist, places it in sdist_directory"""
    logger.info("=== Build sdist called ===")
    logger.info(f"sdist_directory: {sdist_directory}")
    logger.info(f"config_settings: {config_settings}")

    try:
        builder = __get_sdist_builder(
            sdist_directory=sdist_directory, config_settings=config_settings
        )
        logger.info("Builder created successfully")
        with builder.build() as file_path:
            logger.info(f"Sdist built successfully, file_path: {file_path}")
            return file_path.name
    except Exception as e:
        logger.error(f"Error in build_sdist: {e}")
        raise


get_requires_for_build_editable = get_requires_for_build_wheel
# prepare_metadata_for_build_editable = prepare_metadata_for_build_wheel
