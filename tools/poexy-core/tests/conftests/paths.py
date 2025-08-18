import os
import shutil
import uuid
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest
from filelock import FileLock

from poexy_core.utils import platformdirs
from tests.utils.markers import MarkerFile
from tests.utils.paths import TestPath

# pylint: disable=redefined-outer-name


class SamplePaths(Path, Enum):
    Dependencies = Path("dependencies")
    LocalDependencies = Path("dependencies") / "local"
    UrlDependencies = Path("dependencies") / "url"
    GitDependencies = Path("dependencies") / "git"
    CoreFunctionality = Path("core_functionality")
    BinaryPackaging = Path("binary_packaging")
    WheelPackaging = Path("wheel_packaging")
    MetadataFilesLicence = Path("metadata_files") / "license"
    MetadataFilesReadme = Path("metadata_files") / "readme"
    MetadataFilesSource = Path("metadata_files") / "source_files"
    FileManagementInclusions = Path("file_management") / "inclusions"
    FileManagementSymbolicLink = Path("file_management") / "symbolic_link"
    ValidationFilenames = Path("validation") / "filenames"
    ValidationInvalidFormats = Path("validation") / "invalid_formats"
    ValidationInvalidStructure = Path("validation") / "invalid_structure"
    ValidationMissingFiles = Path("validation") / "missing_files"
    ValidationNaming = Path("validation") / "naming"
    EdgeCases = Path("edge_cases")

    def __truediv__(self, other):
        return self.value / other


@pytest.fixture(scope="session")
def samples_path():
    return Path(__file__).parent.parent / "samples"


@pytest.fixture(scope="session")
def self_project_dist_path(tmpdir_factory) -> Path:
    tmpdir = tmpdir_factory.mktemp("dist")
    return Path(tmpdir)


@pytest.fixture(scope="function")
def tmp_root(tmpdir_factory: pytest.TempdirFactory) -> Path:
    base = Path(tmpdir_factory.getbasetemp())
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    path = tmpdir_factory.mktemp(f"test_{uuid.uuid4().hex[:8]}")
    return Path(path)


@pytest.fixture(scope="function")
def dist_path(tmp_root):
    return tmp_root / "dist"


@pytest.fixture(scope="function")
def dist_temp_path(dist_path):
    return dist_path / "temp"


@pytest.fixture(scope="function")
def build_path(tmp_root):
    return tmp_root / "build"


@pytest.fixture(scope="session")
def global_tmp_root(testrun_uid, tmp_path_factory, worker_id, log_info_section) -> Path:
    if worker_id == "master":
        base_tmp = tmp_path_factory.getbasetemp()
    else:
        base_tmp = tmp_path_factory.getbasetemp().parent
    path = base_tmp / "poexy-core-tmp"
    lock_path = str(path) + ".lock"
    lock = FileLock(lock_path)

    def remove_global_tmp_root():
        log_info_section("Removing global tmp root")
        shutil.rmtree(path, ignore_errors=True)

    with lock:
        init_marker = MarkerFile(path / ".initialized", {"testrun_uid": testrun_uid})

        if path.exists() and init_marker.exists():
            marker_data = init_marker.read()
            if marker_data["testrun_uid"] != testrun_uid:
                remove_global_tmp_root()
        elif path.exists() and not init_marker.exists():
            remove_global_tmp_root()

        if not path.exists():
            log_info_section("Creating global tmp root")
            path.mkdir(parents=True, exist_ok=True)

        init_marker.touch()

    try:
        yield path
    finally:
        if init_marker.untouch():
            remove_global_tmp_root()
            log_info_section("Removing test tmp root")
            shutil.rmtree(base_tmp, ignore_errors=True)


@pytest.fixture(scope="session")
def global_virtualenv_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "venv"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def global_virtualenv_archive_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "venv-archive"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def global_virtualenv_lock_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "venv-lock"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def http_server_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "http-server"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def git_server_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "git-server"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def server_lock_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "server-lock"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def samples_lock_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "samples-locks"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def venv_usage_lock_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "venv-usage-lock"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def serial_lock_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "serial-lock"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="function")
def virtualenv_path(tmp_root):
    return tmp_root / "venv"


@pytest.fixture(scope="function", autouse=True)
def pyinstaller_path(tmp_root):
    path = tmp_root / "pyinstaller"
    os.environ["PYINSTALLER_CONFIG_DIR"] = str(path)


@pytest.fixture(scope="function")
def platform_directories(
    dist_package_name,
) -> Callable[[], platformdirs.GenericPlatformDirectories]:
    @cache
    def _platform_directories():
        return platformdirs.GenericPlatformDirectories(dist_package_name())

    return _platform_directories


@pytest.fixture(scope="session", autouse=True)
def file_operations(
    request: pytest.FixtureRequest,
    samples_lock_path,
    create_venv_archive,  # pylint: disable=unused-argument
):
    # Ignore venv fixture. Only present to ensure this fixture runs after venv
    # creation. If we modify file accessibility before the venv is ready, venv
    # installation will fail when trying to access files that have been made
    # inaccessible. This is relevant because poexy-core includes a tests
    # folder containing sample projects that may have their file permissions
    # altered to simulate inaccessible files during testing.
    # This dependency ensures that venv creation completes before file operations
    # are processed. Both fixtures have session scope, but we maintain this dependency
    # to prevent potential regressions where file accessibility modifications could
    # interfere with venv installation.

    file_operations: List[TestPath] = []
    lock_path = samples_lock_path / ".file-operations.lock"
    lock = FileLock(lock_path)

    with lock:
        marker_file = MarkerFile(samples_lock_path / ".file-operations.collected")

        if not marker_file.exists():
            session: pytest.Session = request.node
            for item in session.items:
                for marker in item.own_markers:
                    if marker.name == "file_operation":
                        path = marker.kwargs["path"]
                        if not isinstance(path, TestPath):
                            raise ValueError(
                                f"Expected {type(TestPath)} or subclass, "
                                f"got {type(path)}"
                            )
                        path.prefix_from_pytest_localpath(item.fspath)
                        path.node_id = item.nodeid
                        file_operations.append(path)
            json = [file_operation.to_json() for file_operation in file_operations]
            marker_file.extra = {"operations": json}
        else:
            file_operations_data = marker_file.read()
            operations: List[Dict[str, Any]] = file_operations_data["operations"]
            for operation in operations:
                file_operations.append(TestPath.deserialize(operation))
        marker_file.touch()

    return file_operations


@pytest.fixture(scope="function", autouse=True)
def file_operation(
    request: pytest.FixtureRequest,
    file_operations,
    samples_lock_path,
    serial_test_coordinator,  # pylint: disable=unused-argument
):
    # Ignore serial_test_coordinator fixture. For the same reason explained in
    # file_operations

    function: pytest.Function = request.node

    if len(function.own_markers) == 0:
        yield
        return

    marker_names = [marker.name for marker in function.own_markers]

    if not any(marker_name == "file_operation" for marker_name in marker_names):
        yield
        return

    selected_file_operation: Optional[TestPath] = None

    for file_operation in file_operations:
        if file_operation.node_id == function.nodeid:
            selected_file_operation = file_operation
            break

    if selected_file_operation is None:
        raise ValueError(f"No file operation found for {function.nodeid}")

    sample_path = selected_file_operation.sample_path
    lock_path = samples_lock_path / (sample_path.name + ".lock")
    lock = FileLock(lock_path)

    try:
        # Block test execution (and other tests) until the file operation is complete.
        # This should have minimal impact on other tests since we typically have only
        # two tests per sample path, so contention is limited.
        with lock:
            selected_file_operation.prepare()
            yield
            selected_file_operation.cleanup()
    finally:
        with lock:
            selected_file_operation.cleanup()
