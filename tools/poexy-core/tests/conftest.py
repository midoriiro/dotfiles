import contextlib
import logging
import os
from pathlib import Path
import shutil
import sys
import tarfile
from typing import Callable, Generator, List, Set
import zipfile
from assertpy import assert_that
import pytest

from poexy_core import api
from poexy_core.builders.builder import PythonTag
from poexy_core.builders.sdist import SdistMetadata
from poexy_core.builders.wheel import WheelMetadata
from poexy_core.manifest.manifest import MetadataManifest, PackageInfoManifest, RecordManifest, WheelManifest
from poexy_core.packages.files import FORBIDDEN_DIRS
from poexy_core.packages.format import WheelFormat
from poexy_core.pyproject.toml import PyProjectTOML

from poetry.core.masonry.utils.helpers import distribution_name

from tests.pip import Pip

@pytest.fixture(autouse=True)
def set_logger_level(caplog):
    # Configure the root logger level for tests
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = api.ConsoleHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    # logger.handlers.clear()
    logger.addHandler(console_handler)
    caplog.at_level(logging.INFO)

@pytest.fixture()
def self_project() -> Path:
    project_path = Path(api.__file__).resolve().parent.parent
    return project_path

@pytest.fixture()
def samples_path():
    return Path(__file__).parent / "samples"

@pytest.fixture()
def sample_project(samples_path) -> Callable[[str], Path]:
    def _sample_project(name: str):
        project_path = samples_path / name
        return project_path
    return _sample_project

@pytest.fixture()
def project() -> Callable[[str], Generator[None, None, None]]:
    @contextlib.contextmanager
    def _project(project_path: Path):
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(f"Pyproject.toml not found in {project_path}")

        old_cwd = os.getcwd()
        try:
            os.chdir(project_path)
            yield
        finally:
            os.chdir(old_cwd)
    return _project

@pytest.fixture()
def dist_path(tmp_path):
    return tmp_path / "dist"

@pytest.fixture()
def dist_temp_path(dist_path):
    return dist_path / "temp"

@pytest.fixture()
def build_path(tmp_path):
    return tmp_path / "build"

@pytest.fixture()
def install_path(tmp_path):
    return tmp_path / "install"

@pytest.fixture()
def virtualenv_path(tmp_path):
    return tmp_path / "venv"

@pytest.fixture()
def default_python_tag():
    return PythonTag(
        impl="py",
        major=sys.version_info.major
    )

@pytest.fixture()
def current_python_tag():
    return PythonTag.from_current_environment()

@pytest.fixture()
def pyproject():
    def _pyproject():
        cwd = Path.cwd()
        return PyProjectTOML(path=cwd)
    return _pyproject

@pytest.fixture()
def package_name(pyproject) -> Callable[[], str]:
    def _package_name():
        return pyproject().poetry.package.name
    return _package_name

@pytest.fixture()
def dist_package_name(pyproject) -> Callable[[], str]:
    def _dist_package_name():
        return distribution_name(pyproject().poetry.package.name)
    return _dist_package_name

@pytest.fixture()
def package_version(pyproject) -> Callable[[], str]:
    def _package_version():
        return pyproject().poetry.package.version.to_string()
    return _package_version

@pytest.fixture()
def site_packages_path(install_path) -> Path:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    return install_path / "lib" / f"python{python_version}" / "site-packages"

@pytest.fixture()
def wheel_metadata(dist_temp_path, dist_package_name, package_version) -> Callable[[PythonTag], WheelMetadata]:
    def _wheel_metadata(python_tag: PythonTag) -> WheelMetadata:
        wheel_metadata = WheelMetadata(
            dist_temp_path, 
            dist_package_name(), 
            package_version(), 
            python_tag
        )
        assert_that(str(wheel_metadata.archive_path)).exists()
        return wheel_metadata
    return _wheel_metadata

@pytest.fixture()
def wheel_data_purelib_folder(wheel_metadata) -> Callable[[PythonTag], Path]:
    def _wheel_data_purelib_folder(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        data_purelib_folder = metadata.data_purelib_folder
        data_purelib_folder = data_purelib_folder.relative_to(metadata.root_folder)
        return data_purelib_folder
    return _wheel_data_purelib_folder

@pytest.fixture()
def wheel_data_scripts_folder(wheel_metadata) -> Callable[[PythonTag], Path]:
    def _wheel_data_scripts_folder(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        data_scripts_folder = metadata.data_scripts_folder
        data_scripts_folder = data_scripts_folder.relative_to(metadata.root_folder)
        return data_scripts_folder
    return _wheel_data_scripts_folder

@pytest.fixture()
def sdist_metadata(dist_temp_path, dist_package_name, package_version) -> Callable[[], SdistMetadata]:
    def _sdist_metadata():
        sdist_metadata = SdistMetadata(
            dist_temp_path, 
            dist_package_name(), 
            package_version()
        )
        assert_that(str(sdist_metadata.archive_path)).exists()
        return sdist_metadata
    return _sdist_metadata

@pytest.fixture()
def assert_metadata_manifest(wheel_metadata, package_name, package_version) -> Callable[[PythonTag], MetadataManifest]:
    def _assert(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        metadata_manifest = MetadataManifest(metadata.dist_info_folder)
        metadata_manifest.read()
        assert_that(metadata_manifest.get("Metadata-Version")).is_equal_to("2.4")
        assert_that(metadata_manifest.get("Name")).is_equal_to(package_name())
        assert_that(metadata_manifest.get("Version")).is_equal_to(package_version())
        return metadata_manifest
    return _assert

@pytest.fixture()
def assert_wheel_manifest(wheel_metadata) -> Callable[[PythonTag], WheelManifest]:
    def _assert(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        wheel_manifest = WheelManifest(metadata.dist_info_folder)
        wheel_manifest.read()
        assert_that(wheel_manifest.get("Wheel-Version")).is_equal_to("1.0")
        assert_that(wheel_manifest.get("Generator")).is_equal_to("Poexy")
        if python_tag.platform is None:
            assert_that(wheel_manifest.get("Root-Is-Purelib")).is_equal_to("true")
        else:
            assert_that(wheel_manifest.get("Root-Is-Purelib")).is_equal_to("false")
        assert_that(wheel_manifest.get("Tag")).is_equal_to(f"{python_tag}")
        return wheel_manifest
    return _assert

@pytest.fixture()
def assert_record_manifest(wheel_metadata) -> Callable[[PythonTag], RecordManifest]:
    def _assert(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        record_manifest = RecordManifest(metadata.dist_info_folder)
        record_manifest.read()
        assert_that(len(record_manifest)).is_greater_than(1)
        for record in record_manifest:
            assert_that(FORBIDDEN_DIRS).does_not_contain(*record.path.parts)
        return record_manifest
    return _assert

@pytest.fixture()
def assert_pkginfo_manifest(sdist_metadata, package_name, package_version) -> Callable[[PythonTag], PackageInfoManifest]:
    def _assert():
        metadata = sdist_metadata()
        pkginfo_manifest = PackageInfoManifest(metadata.root_folder)
        pkginfo_manifest.read()
        assert_that(pkginfo_manifest.get("Metadata-Version")).is_equal_to("2.4")
        assert_that(pkginfo_manifest.get("Name")).is_equal_to(package_name())
        assert_that(pkginfo_manifest.get("Version")).is_equal_to(package_version())
        return pkginfo_manifest
    return _assert

@pytest.fixture(autouse=True)
def pip(virtualenv_path) -> Pip:
    pip = Pip(virtualenv_path)
    pip.create_virtualenv()
    return pip

@pytest.fixture(autouse=True)
def self_install(pip, project, self_project, dist_path):
    with project(self_project):
        filename = api.build_wheel(str(dist_path))
        archive_path = dist_path / filename
        assert_that(str(archive_path)).is_file()
        assert_that(zipfile.is_zipfile(archive_path)).is_true()
        pip.install(archive_path)

@pytest.fixture()
def assert_pip_wheel(build_path, pip) -> Callable[[Path], Path]:
    def _assert(archive_path: Path):
        wheel_path = Path(build_path) / "wheel"
        returncode = pip.wheel(archive_path, wheel_path)
        destination_path = Path.cwd() / "dist" / "test.whl"
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(archive_path, destination_path)
        assert_that(returncode).is_equal_to(0)
        return wheel_path
    return _assert

@pytest.fixture()
def assert_pip_install(install_path, pip) -> Callable[[Path], Path]:
    def _assert(archive_path: Path):
        returncode = pip.install(archive_path, install_path)
        destination_path = Path.cwd() / "dist" / "test.whl"
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(archive_path, destination_path)
        assert_that(returncode).is_equal_to(0)
        return install_path
    return _assert

@pytest.fixture()
def assert_tar_file() -> Callable[[Path, List[Path], bool], None]:
    def _assert(archive_path: Path, expected_files: List[Path], strict: bool = False):
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()
            assert_that(members).is_not_empty()

            archive_file_paths = [
                Path(member.name)
                for member in members
            ]

            for member in archive_file_paths:
                if member.name == "PKG-INFO":
                    root_folder = member.parent
                    break

            assert_that(root_folder).is_not_none()
            
            archive_file_paths = [
                Path(member.name).relative_to(root_folder) 
                for member in members
            ]
            
            if strict:
                # Assert that all expected files are present and no extra files exist
                archive_file_paths = [
                    path
                    for path in archive_file_paths
                    if path.name not in ["PKG-INFO", "pyproject.toml"]
                ]
                assert_that(len(archive_file_paths)).is_equal_to(len(expected_files))
                assert_that(sorted(archive_file_paths)).is_equal_to(sorted(expected_files))
            else:
                # Assert that all expected files are present (partial check)
                for expected_file in expected_files:
                    assert_that(archive_file_paths).contains(expected_file)
    return _assert

@pytest.fixture()
def assert_zip_file() -> Callable[[Path, List[Path], bool], None]:
    def _assert(
        archive_path: Path, 
        expected_files: List[Path], 
        strict: bool = False, 
        strip: bool = True
    ):
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            members = zip_file.namelist()
            assert_that(members).is_not_empty()

            archive_file_paths = [
                Path(member)
                for member in members
            ]
            
            if strict:
                # Assert that all expected files are present and no extra files exist
                if strip:
                    archive_file_paths = [
                        path
                        for path in archive_file_paths
                        if path.name not in ["WHEEL", "METADATA", "RECORD"]
                    ]
                assert_that(len(archive_file_paths)).is_equal_to(len(expected_files))
                assert_that(sorted(archive_file_paths)).is_equal_to(sorted(expected_files))
            else:
                # Assert that all expected files are present (partial check)
                for expected_file in expected_files:
                    assert_that(archive_file_paths).contains(expected_file)
    return _assert


@pytest.fixture()
def assert_wheel_build(
    project,
    dist_path,  
    install_path,
    dist_package_name,
    package_name,
    site_packages_path,
    current_python_tag,
    default_python_tag,
    wheel_metadata,
    wheel_data_scripts_folder,
    assert_metadata_manifest,
    assert_wheel_manifest,
    assert_record_manifest,
    assert_pip_wheel,
    assert_pip_install,
    assert_zip_file
) -> Callable[[Path], Callable[[List[Path], bool], None]]:
    def _assert(project_path: Path, format: Set[WheelFormat] = {WheelFormat.Source}):
        with project(project_path):
            filename = api.build_wheel(str(dist_path))

            assert_that(filename).ends_with('.whl')
            assert_that(filename).starts_with(dist_package_name())
            archive_path = dist_path / filename
            assert_that(str(archive_path)).is_file()
            assert_that(zipfile.is_zipfile(archive_path)).is_true()

            if len(format) == 1 and WheelFormat.Binary in format:
                python_tag = current_python_tag
            else:
                python_tag = default_python_tag

            metadata: WheelMetadata = wheel_metadata(python_tag)
            assert_metadata_manifest(python_tag)
            assert_wheel_manifest(python_tag)
            assert_record_manifest(python_tag)
            assert_pip_wheel(archive_path)
            assert_pip_install(archive_path)

            site_packages = site_packages_path / dist_package_name()

            if len(format) == 1 and WheelFormat.Binary in format:
                assert_that(str(site_packages)).does_not_exist()
                binary_path = install_path / "bin" / package_name()
                assert_that(binary_path.exists()).is_true()
                dist_info_folder = metadata.dist_info_folder.name
                assert_zip_file(
                    archive_path,
                    [
                        Path(dist_info_folder) / "WHEEL",
                        Path(dist_info_folder) / "METADATA",
                        Path(dist_info_folder) / "RECORD",
                        wheel_data_scripts_folder(python_tag) / package_name(),
                    ],
                    strict=True,
                    strip=False
                )
            else:
                assert_that(str(site_packages)).exists()
                binary_path = install_path / "bin" / package_name()
                if WheelFormat.Binary in format:
                    assert_that(binary_path.exists()).is_true()
                else:
                    assert_that(binary_path.exists()).is_false()
                dist_info_folder = metadata.dist_info_folder.name
                expected_zip_files = [
                    Path(dist_info_folder) / "WHEEL",
                    Path(dist_info_folder) / "METADATA",
                    Path(dist_info_folder) / "RECORD",
                ]
                if WheelFormat.Binary in format:
                    expected_zip_files.append(
                        wheel_data_scripts_folder(python_tag) / package_name()
                    )
                assert_zip_file(
                    archive_path,
                    expected_zip_files
                )

            def _assert_zip_file(expected_files: List[Path], strict: bool = False):
                assert_zip_file(archive_path, expected_files, strict)
            return _assert_zip_file
    return _assert

@pytest.fixture()
def assert_sdist_build(
    project,
    dist_path,
    site_packages_path,
    install_path,
    dist_package_name,
    package_name,
    assert_pkginfo_manifest,
    assert_pip_wheel,
    assert_pip_install,
    assert_tar_file
) -> Callable[[Path], Callable[[List[Path], bool], None]]:
    def _assert(project_path: Path, format: Set[WheelFormat] = {WheelFormat.Source}):
        with project(project_path):
            filename = api.build_sdist(str(dist_path))
    
            assert_that(filename).ends_with('.tar.gz')
            assert_that(filename).starts_with(dist_package_name())
            archive_path = dist_path / filename
            assert_that(str(archive_path)).is_file()
            assert_that(tarfile.is_tarfile(archive_path)).is_true()

            assert_pkginfo_manifest()
            assert_pip_wheel(archive_path)
            assert_pip_install(archive_path)

            site_packages = site_packages_path / dist_package_name()

            if len(format) == 1 and WheelFormat.Binary in format:
                assert_that(str(site_packages)).does_not_exist()
                binary_path = install_path / "bin" / package_name()
                assert_that(binary_path.exists()).is_true()
            else:
                assert_that(str(site_packages)).exists()
                binary_path = install_path / "bin" / package_name()
                if WheelFormat.Binary in format:
                    assert_that(binary_path.exists()).is_true()
                else:
                    assert_that(binary_path.exists()).is_false()

            assert_tar_file(
                archive_path,
                [
                    Path("pyproject.toml"),
                    Path("PKG-INFO")
                ]
            )

            def _assert_tar_file(expected_files: List[Path], strict: bool = False):
                assert_tar_file(archive_path, expected_files, strict)
            return _assert_tar_file
    return _assert