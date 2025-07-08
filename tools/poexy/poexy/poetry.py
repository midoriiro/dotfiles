import configparser
import logging
from pathlib import Path
import shutil
import sys
import tomllib
import zipfile


from poexy import safe_command
from poexy.safe_print import safe_print_done, safe_print_error, safe_print_info, safe_print_start, safe_print_success
from poexy.wheel import WheelBuilder

logger = logging.getLogger(__name__)

class PoetryProjectError(Exception):
    pass


def get_executable_size(project_path: Path, executable_name: str) -> int:
    distribuable_path = project_path / "dist"
    executable_path = distribuable_path / executable_name
    return executable_path.stat().st_size


def clean_directories(project_path: Path):
    build_path = project_path / "build"
    dist_path = project_path / "dist"
    if build_path.exists():
        shutil.rmtree(build_path)
    if dist_path.exists():
        shutil.rmtree(dist_path)

def build(project_path: Path):
    safe_print_start(
        f"Running 'poetry build'...", 
        printer=logger.info
    )
    exit_code = safe_command.run(
        ["poetry", "build"], 
        printer=logger.info, 
        error_printer=logger.error,
        cwd=project_path
    )
    if exit_code != 0:
        raise PoetryProjectError("Failed to build Poetry project")
    
    safe_print_done("Poetry build finished successfully", printer=logger.info)


def build_executable(
    project_path: Path,
    package_path: Path, 
    entry_point: str,
    executable_name: str, 
):
    safe_print_start(
        f"Building executable '{executable_name}'...", 
        printer=logger.info
    )
    path_to_entry_point = str(project_path / package_path / entry_point)
    spec_path = str(project_path / "build")
    dist_path = str(project_path / "dist")
    work_path = str(project_path / "build" / "temp")

    command = [
        "poetry",
        "run",
        "pyinstaller",
        path_to_entry_point,
        '--onefile',
        '--name', executable_name,
        '--specpath', spec_path,          
        '--distpath', dist_path,
        '--workpath', work_path,
        '--collect-submodules', str(package_path),
        '--strip',
        '--clean',
    ]

    exit_code = safe_command.run(
        command, 
        printer=logger.info, 
        error_printer=logger.error,
        cwd=project_path
    )

    if exit_code != 0:
        raise PoetryProjectError("Failed to build executable")

    safe_print_done("Executable built successfully", printer=logger.info)


def package_wheel(
    project_path: Path,
    project_name: str,
    project_version: str,
    executable_name: str,
):
    """Add executable to wheel and tar.gz packages."""
    
    distribuable_path = project_path / "dist"
    executable_path = distribuable_path / executable_name

    if not executable_path.exists():
        raise PoetryProjectError(f"Executable not found at '{executable_path}'")
    
    safe_print_start(
        "Packaging executable...", 
        printer=logger.info
    )

    wheel_file_filter = f"*{project_version}*.whl"
    distribuable_files = list(distribuable_path.glob(wheel_file_filter))

    if len(distribuable_files) == 0:
        raise PoetryProjectError(f"No distribuable files found at '{distribuable_path}'")
    
    safe_print_info(
        f"Adding executable to {len(distribuable_files)} package(s)...", 
        printer=logger.info
    )
    
    # Add to wheel packages
    for distribuable_file in distribuable_files:
        with WheelBuilder.extract(distribuable_file, project_name, project_version) as builder:
            builder.manifests.metadata.set_required_python_version(
                f"=={sys.version_info.major}.{sys.version_info.minor}.*"
            )
            builder.manifests.metadata.set_platform(builder.metadata.platform)
            builder.manifests.metadata.set_supported_platform(builder.metadata.platform)
            builder.manifests.metadata.delete_requires_dist()
            builder.manifests.metadata.delete_classifiers(
                "Classifier",
                lambda v: not v.endswith(f"Python :: {sys.version_info.major}.{sys.version_info.minor}")
            )
            builder.manifests.wheel.set_root_is_purelib(False)
            builder.manifests.wheel.set_tag(builder.metadata.tag)
            builder.manifests.record.delete(
                builder.metadata.dist_info_folder / "entry_points.txt"
            )
            builder.manifests.record.set(
                source=executable_path,
                destination=builder.metadata.data_scripts_folder / executable_name
            )
            builder.build()
        
    safe_print_done("Executable packaged successfully", printer=logger.info)