# Poexy-Core

[![Python Version](https://img.shields.io/badge/python-3.9--3.13-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2025.7.4-green.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](tests/)
[![PEP 517](https://img.shields.io/badge/PEP%20517-compliant-blue.svg)](https://peps.python.org/pep-0517/)
[![PEP 518](https://img.shields.io/badge/PEP%20518-compliant-blue.svg)](https://peps.python.org/pep-0518/)
[![PEP 639](https://img.shields.io/badge/PEP%20639-compliant-blue.svg)](https://peps.python.org/pep-0639/)
[![PEP 660](https://img.shields.io/badge/PEP%20660-compliant-blue.svg)](https://peps.python.org/pep-0660/)

**Poexy-Core** is an advanced Python build backend that extends the capabilities of Python packaging beyond traditional wheels and source distributions. It provides a unified solution for building traditional Python packages and standalone executable applications using PyInstaller, all while maintaining full PEP 517/518/639/660 compliance.

## 📋 Table of Contents

- [🚀 Quick Start](#quick-start)
- [🚀 Features](#features)
- [📋 Requirements](#requirements)
- [📦 Installation](#installation)
- [📖 Usage Examples](#usage-examples)
- [🔧 Configuration Reference](#configuration-reference)
- [🏗️ Building Packages](#building-packages)
- [🧪 Testing](#testing)
- [📁 Project Structure](#project-structure)
- [❓ FAQ & Known Issues](#faq--known-issues)
- [🔧 Troubleshooting](#troubleshooting)
- [🤝 Contributing](#contributing)
- [📄 License](#license)
- [🎯 Why Choose Poexy-Core?](#why-choose-poexy-core)
- [🙏 Acknowledgments](#acknowledgments)
- [📞 Support](#support)

<a id="quick-start"></a>
## 🚀 Quick Start

### 1. Create a Basic Project

```bash
mkdir my-project && cd my-project
touch pyproject.toml
mkdir -p src/my_package
touch src/my_package/__init__.py
echo 'def main(): print("Hello, World!")' > src/my_package/main.py
```

### 2. Configure `pyproject.toml`

```toml
[project]
name = "my-project"
version = "1.0.0"
description = "My awesome project"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_package]
source = "src"
```

### 3. Build Your Package

```bash
pip install build
python -m build
```

That's it! You'll get both a wheel (`.whl`) and source distribution (`.tar.gz`) in the `dist/` directory.

### Migrating from Poetry

1. Keep your existing `pyproject.toml`
2. Update build system:
   ```toml
   [build-system]
   - requires = ["poetry-core"]
   - build-backend = "poetry.core.masonry.api"
   + requires = ["poexy-core"]
   + build-backend = "poexy_core.api"
   ```
3. Add Poexy configuration if needed

<a id="features"></a>
## 🚀 Features

### Multi-Format Package Support
- **Wheels**: Standard Python packages (source and binary formats)
- **SDist**: Source distributions (tar.gz archives)
- **Binary**: Standalone executables via PyInstaller integration

### Advanced Configuration
- Extended `pyproject.toml` syntax with `[tool.poexy]` sections
- Granular file inclusion/exclusion control
- Flexible package format configuration
- Type-safe configuration validation with Pydantic

### PEP 517/518 Compliance
- Standard build backend interface
- Compatible with `pip`, `build`, and other packaging tools
- Seamless integration with existing Python workflows

### PyInstaller Integration
- Automatic executable generation
- Support for `onefile` and `onedir` modes
- Automatic entry point detection
- Configurable build options

> **Note:** About PyInstaller
>
> - `onedir` mode not yet supported
> - Currently, there are no available options to customize the PyInstaller build process for your executable.

<a id="requirements"></a>
## 📋 Requirements

- Python 3.9 to 3.13
- Poetry Core 2.1.0+
- Pydantic 2.11.7+
- PyInstaller 6.14.2+
- Rich 14.0.0+
- VirtualEnv 20.31.2+
- UV 0.8.5+

<a id="installation"></a>
## 📦 Installation

### Using pip

```bash
pip install poexy-core
```

### Using Poetry

```bash
poetry add --group=build poexy-core
```

### From Source

```bash
git clone https://github.com/your-repo/poexy-core.git
cd poexy-core
pip install -e .
```

<a id="usage-examples"></a>
## 📖 Usage Examples

### 1. Traditional Python Library

Perfect for libraries you want to distribute on PyPI:

```toml
[project]
name = "my-awesome-library"
version = "1.0.0"
description = "An awesome Python library"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_awesome_library]
source = "src"
```

**Builds:** Standard wheel (`.whl`) + source distribution (`.tar.gz`)  
**Use case:** Libraries, packages for PyPI

### 2. CLI Application as Binary

Create a standalone executable that users can run without Python installed:

```toml
[project]
name = "my-cli-tool"
version = "1.0.0"
description = "A useful CLI tool"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_cli_tool]
source = "src"

[tool.poexy.wheel]
format = ["binary"]

[tool.poexy.binary]
name = "my-tool"
entry_point = "src.main"
```

**Builds:** Standalone executable (`.whl` package will not contains any python code)  
**Use case:** CLI tools, desktop applications

### 3. Hybrid Package (Library + Binary)

Distribute both a Python library and a CLI tool in one package:

```toml
[project]
name = "my-hybrid-package"
version = "1.0.0"
description = "A library with CLI tool"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_hybrid_package]
source = "src"

[tool.poexy.wheel]
format = ["source", "binary"]

[tool.poexy.binary]
name = "my-cli"
```

**Builds:** Wheel with Python library + embedded binary  
**Use case:** Libraries that also provide CLI tools

> **💡 Tip:** With hybrid packages, users get both:
> - A Python library they can `import` in their code
> - A CLI binary automatically installed to their `$PATH`

### 4. Custom Entry Points

Specify exactly how your binary should start:

```toml
[tool.poexy.binary]
name = "my-app"
entry_point = "src.cli"  # Points to __main__ function in src/cli.py
```

### 5. Advanced File Management

Control exactly which files are included in your packages:

```toml
[project]
name = "my-package"
version = "1.0.0"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_package]
source = "src"

# Include extra files in source distribution
[tool.poexy.sdist]
includes = [
    "docs",           # Include entire docs/ directory
    "examples",       # Include examples/ directory
    "CHANGELOG.md"    # Include specific files
]

# Control wheel contents precisely
[tool.poexy.wheel]
includes = [
    { path = "docs", destination = "data" },
    { path = "config", destination = "config" }
]
excludes = [
    "tests",          # Exclude test files
    "docs/**/*.rst",  # Exclude specific patterns
    "*.txt"           # Exclude by extension
]
```

**Result:**
- **Source distribution:** Includes docs, examples, and changelog
- **Wheel:** Places docs in `$prefix/share/my-package/docs` and config in `$prefix/etc/my-package/` on Linux systems

> **Note:** All included files are mapped to platform-specific directories under the installation prefix. See [platform-specific configuration](#platform-directories) for detailed platform directory mappings.

> **Default exclusions** 
>
> The following directories are automatically excluded from all packages and do not need to be specified in `excludes`:
> - `__pycache__`
> - `build`
> - `dist`
> - `.eggs`
> - `.mypy_cache`
> - `.pytest_cache`
> - `.venv`
> - `venv`
>
> These directories are considered build artifacts, cache files, or development environments and are filtered out by default.
>
> When building wheels, only files with the following extensions are included by default:
> - `.py` (Python source files)
> - `.pyd` (Python extension modules on Windows)
> - `.so` (Python extension modules on Linux/macOS)
> - `.dll` (Dynamic link libraries on Windows)
> - `.dylib` (Dynamic libraries on macOS)

#### Including symbolic links

You can include a symlink just like a regular file. The link must:
- Resolve inside the project base (no escaping),
- Not be broken,
- Point to a readable file or directory.

Example (wheel):

```toml
[tool.poexy.wheel]
includes = [
    # "assets/config-link.json" is a symlink (prefer relative) to a file inside the project
    { path = "assets/config-link.json", destination = "share/assets" }
]
```

Example (sdist):

```toml
[tool.poexy.sdist]
includes = [
    # Include a symlink; it will be validated and resolved during packaging
    "assets/config-link.json"
]
```

> **Notes:** 
> - Relative symlinks are recommended.
> - Escaping (pointing outside the project), broken links, or unreadable targets will fail the build.

<a id="platform-directories"></a>
#### Platform Directories (Wheel Only)

When building wheels, you can specify where files should be installed using the `destination` field. This allows precise control over file placement in the target system.

Example (wheel with platform directories):

```toml
[tool.poexy.wheel]
includes = [
    # Configuration files go to platform data directory
    { path = "app.json", destination = "data" },
    
    # Static assets go to shared resources  
    { path = "assets/**/*", destination = "config" },
    
    # Cache templates go to cache directory
    { path = "templates/**/*", destination = "cache" }
]
```

Available platform directories:
- `data`    - Application data files (platform-specific data)
- `config`  - Application configuration resources and assets
- `cache`   - Application Cache files and temporary resources

Example file placement results:
```
# Input files examples by platform:

# Linux:
assets/logo.png     → ${prefix}/share/my_package/assets/logo.png
app.json            → ${prefix}/etc/my_package/app.json
templates/base.html → ${prefix}/var/cache/my_package/cache/templates/base.html

# macOS:
assets/logo.png     → ${prefix}/Application Support/my_package/assets/logo.png
app.json            → ${prefix}/Preferences/my_package/app.json
templates/base.html → ${prefix}/Caches/my_package/cache/templates/base.html

# Windows:
assets/logo.png     → ${prefix}/my_package/share/assets/logo.png
app.json            → ${prefix}/my_package/config/app.json
templates/base.html → ${prefix}/my_package/cache/templates/base.html
```

> **Notes:**
> - Platform directories are only supported for wheel packages, not source distributions
> - Files without a `destination` are automatically placed based on their type and location
> - Platform directories follow the wheel specification for data file placement

#### Automatic File Type Detection

Poexy-Core automatically determines the optimal placement for files based on their location and type, reducing the need for manual configuration:

**Source files** (files under the source directory):
- Placed in `purelib` (pure Python library directory)
- Example: `src/my_package/module.py` → `{site-packages}/my_package/module.py`

**Platform files** (files outside the source directory):
- Automatically treated as platform-specific content
- Placed in `data` directory by default if no `destination` is specified

**Symbolic links**:
- Validated for security:
  - no cross-references between the source directory and other directories within the project (including cross-references between platform-specific directories)
  - no symlinks escaping the project directory, including escapes detection during symlink chain resolution
  - no symlink cycles (no self-loops or multi-node cycles)
  - no broken symlinks
  - all symlink targets are readable
- Resolved and packaged based on their target type
- Relative symlinks are preferred for portability

**Binary files** (`.so`, `.dll`, `.dylib`):
- Automatically detected and placed in appropriate platform-specific locations
- Handled according to wheel specification requirements

This automatic detection ensures optimal package structure without requiring extensive manual configuration, while still allowing fine-grained control when needed through explicit `destination` settings.

### 6. Complex Dependencies

Poexy-Core handles various complex dependency scenarios that are common in real-world projects:

#### Mixed Local and Remote Dependencies

```toml
[project]
dependencies = [
    # Remote PyPI packages
    "click>=8.0.0",
    "pydantic>=2.0.0",
    
    # Local file dependency
    "my-utils @ file:///path/to/local/my-utils-1.0.0.tar.gz",
    
    # VCS dependency
    "my-utils @ git+https://github.com/user/my-utils.git@v1.2.3",
]

[tool.poexy.binary.my_app]
entrypoint = "my_app.cli"
```

> **Notes:** When generating binaries, if there are conflicts between local and remote dependencies (as shown in the example above), Poexy-Core will attempt to install only the most recent version (if the version can be determined). If version comparison is not possible, the remote version will be installed by default.

### Editable Installs (Development Mode)

For development, you can create editable installs that link to your source directory instead of copying files. This allows you to modify your code without reinstalling the package:

```toml
[project]
name = "my-package"
version = "1.0.0"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_package]
source = "src"
```

Install in editable mode using pip:

```bash
pip install -e .
```

> **Note:** Editable installs work by creating a `.pth` file in the wheel that points to your source directory. This means your package files remain in their original location and changes are immediately available without reinstallation.

> **Compatibility:** Editable installs are compatible with any `pyproject.toml` configuration that can build regular wheels. The same configuration is used for both standard and editable installs.

<a id="configuration-reference"></a>
## 🔧 Configuration Reference

### Package Configuration

```toml
[tool.poexy.package.my_package]
source = "src"  # Source directory
```

> **Note:** Package name
>
> Package name should be in form of a distribution name as defined [here](https://packaging.python.org/en/latest/specifications/binary-distribution-format/#escaping-and-unicode)

### Wheel Configuration

```toml
[tool.poexy.wheel]
format = ["source", "binary"]  # Available formats
includes = []  # Additional files to include
excludes = []  # Files to exclude
```

### Binary Configuration

```toml
[tool.poexy.binary]
name = "my-app"  # Executable name
entry_point = "src.main"  # Entry point (optional, auto-detected if not specified)
```

### SDist Configuration

```toml
[tool.poexy.sdist]
includes = []  # Additional files to include
excludes = []  # Files to exclude
```

<a id="building-packages"></a>
## 🏗️ Building Packages

### Using build directly

```bash
pip install build
python -m build
```

or 

```bash
python -m build --wheel
python -m build --sdist
```

### Using Poetry

```bash
poetry build
```

### Using UV

```bash
poetry run uv build
```

or 

```bash
uv build
```

if installed at system level.

<a id="testing"></a>
## 🧪 Testing

### Running Tests

```bash
# Run all tests
poetry run pytest tests

# Run with coverage
poetry run pytest tests --cov=poexy_core

# Run tests in parallel
poetry run pytest tests --numprocesses=auto
```

### Helper Scripts

Two helper scripts are provided for common local workflows:

- scripts/test-default.sh
  - Purpose: run a representative test with verbose output and timings
  - Default behavior: executes `tests/test_binary_name.py::test_wheel`
  - Usage:
    ```bash
    bash scripts/test-default.sh
    ```

- scripts/test-repeat-setup.sh
  - Purpose: exercise and measure the setup phase repeatedly (useful to benchmark environment bootstrap performance and caching behavior)
  - Parameter: edit N in the script to control the number of repetitions (default: 1000)
  - Default behavior: runs `pytest --setup-only` on `tests/cases/core_functionality/test_default.py::test_wheel` in a loop
  - Usage:
    ```bash
    bash scripts/test-repeat-setup.sh
    ```

### Test Structure

The test suite uses sample projects and comprehensive fixtures:

#### **Sample Projects (`tests/samples/`)**
Real project configurations used for testing different scenarios.

#### **Test Fixtures (`tests/conftests/`)**
Shared testing utilities:
- `project.py` - Project setup and context management
- `assert_builds.py` - Build assertion utilities
- `assert_manifests.py` - Manifest validation
- `metadata.py` - Metadata testing
- `paths.py` - Path management
- `pip.py` - Pip integration testing
- `logger.py` - Logging utilities
- `servers` - HTTP and Git servers

#### **Test Files**
Each test file follows the same pattern:
- Uses a sample project via `sample_project()` fixture
- Tests both wheel and sdist builds
- Validates installation and file contents if necessary

> **Note:** See the test files for concrete examples

**Pattern:**
```python
@pytest.fixture()
def project_path(sample_project):
    return sample_project("sample_name")

def test_wheel(project, project_path, assert_wheel_build, ...):
    with project(project_path):
        # Build wheel and validate contents
        assert_zip_file = assert_wheel_build(project_path)
        # Assert files in zip file and venv paths...

def test_sdist(project, project_path, assert_sdist_build, ...):
    with project(project_path):
        # Build sdist and validate contents
        assert_tar_file = assert_sdist_build(project_path)
        # Assert files in tar file and venv paths...
```

### Test Infrastructure

Key takeaways (philosophy):
- Fast feedback: the suite is designed to run in parallel and keep per-test setup minimal.
- Predictable and safe: isolation is the default; shared resources are explicit and centrally managed.
- Smart reuse: heavy, repeatable work is done once and reused to save time and energy.
- Declarative control: tests express needs with simple markers; the infrastructure handles orchestration.
- Scale-friendly: the same approach works locally and on CI with many workers, without flakiness.

This section details the testing infrastructure beyond the generic pattern above.

- **High-level layout**
  - `tests/cases/`: Spec-level tests organized by feature area
  - `tests/samples/`: Realistic sample projects used as test inputs
  - `tests/conftest.py`: Global `pytest` configuration and marker registration
  - `tests/conftests/`: Reusable fixtures (assertions, project/session setup, servers, logging)
  - `tests/utils/`: Test-only helpers (paths, markers, local servers, virtualenv wrapper)

- **Project and working-directory management**
  - `project()` context manager fixture from `conftests/project.py` switches `cwd` to the sample project root and restores it afterwards; it validates the presence of `pyproject.toml` before yielding
  - `pyproject()` provides a typed reader (`PyProjectTOML`) of the current project's configuration

- **Virtual environment strategy**
  - A single, reusable venv is created once per test session, archived, and reused by individual tests to minimize setup time
  - Session-scoped archive creation happens via `create_venv_archive` (see `conftests/pip.py`), which:
    - Creates a venv under a session-wide path (`global_virtualenv_path`)
    - Either builds and installs Poexy-Core into that venv or installs only build requirements depending on `venv_self_build_usage`
    - Produces a compressed archive (`venv.tar.zst`) stored in `global_virtualenv_archive_path`
    - Coordinates exclusive creation with a `FileLock` and a `MarkerFile` to be safe across parallel workers
  - Per-test venv extraction via `venv` fixture uses `TestVirtualEnvironment.create_from_archive(...)` to inflate the archived venv into a test-local directory, ensuring isolation and speed; it also adjusts script shebangs to the new path
  - `pip` fixture wraps pip/uv via `PackageInstallerProgram` and asserts the expected base packages are present

- **Build and manifest assertions** (`conftests/assert_builds.py`, `conftests/assert_manifests.py`)
  - `assert_wheel_build(...)` and `assert_sdist_build(...)` orchestrate end-to-end builds via the public backend API (`api.build_wheel`, `api.build_sdist`, `api.build_editable`) inside the `project()` context
  - They validate generated archives, parse and assert manifests (`METADATA`, `WHEEL`, `RECORD`, `PKG-INFO`) and perform real `pip install` into the test venv
  - Utilities `assert_zip_file` and `assert_tar_file` support strict/partial content checks, including optional stripping of standard metadata entries

- **Temporary path management** (`conftests/paths.py`)
  - Function-scoped paths like `tmp_root`, `dist_path`, `dist_temp_path`, `build_path` are provided per test for clean, isolated build artifacts
  - `SamplePaths` enumerates root directories within `tests/samples/` for discoverability and consistency across tests

- **Local servers for dependency scenarios** (`conftests/servers.py`, `tests/utils/servers.py`)
  - Session-scoped HTTP and Git servers can be enabled via markers (`use_http_server`, `use_git_server`) and are started only if needed
  - Servers are started on localhost ports 8000 (HTTP) and 8001 (Git), guarded by `FileLock` and `MarkerFile` to avoid duplication and races in parallel runs
  - Robust startup/shutdown with port detection, process group handling, and retry/cleanup logic ensures stability on CI and local machines

- **File-operation orchestration for edge cases** (`tests/utils/paths.py`)
  - Tests that need to manipulate filesystem states (unreadable files, symlinks, cycles, escapes) use `@pytest.mark.file_operation(path=...)` with a `TestPath` instance to declare the operation
  - Session fixture `file_operations` pre-collects all declared operations; function-scoped `file_operation` executes the matching operation with exclusive locking per sample
  - Provided implementations include `InaccessiblePath`, `SymlinkPath`, `BrokenSymlinkPath`, `SymlinkSelfLoopPath`, `SymlinkChainCyclePath` (multi-node cycles), `SymlinkEscapingPath`, `SymlinkPointsToUnreadableFilePath`
  - This design ensures deterministic setup/teardown even under `pytest-xdist` parallelization

  - Base class `TestPath`
    - Purpose: describes a filesystem manipulation bound to a test sample path
    - Lifecycle hooks: implement `prepare()` (before test body) and `cleanup()` (after test body)
    - Context binding: `prefix_from_pytest_localpath(...)` is called by the infra to resolve your relative `path` against the matching `tests/samples/...` directory that mirrors `tests/cases/...`
    - Sample resolution: computes `sample_path` and `sample_src_path` (either `...<sample_name>/src` or `.../<sample_name>`) for convenience (where src is the source directory of that sample project)
    - Association: the infra sets `node_id` for the test item so the right operation runs for the right test
    - Serialization: `to_json()` / `deserialize()` allow passing instances across workers using simple JSON (you can store extra fields)

    Example of extending `TestPath`:

    ```python
    from pathlib import Path
    from typing import Any, Dict, override
    import os
    from tests.utils.paths import TestPath

    class ReplaceFileContentPath(TestPath):
        def __init__(self, path: str, new_content: str):
            super().__init__(path)
            self._new_content = new_content
            self._backup_content: str | None = None

        @override
        def to_json(self) -> Dict[str, Any]:
            data = super().to_json()
            data["new_content"] = self._new_content
            data["backup_content"] = self._backup_content
            return data

        @override
        def from_json(self, data: Dict[str, Any]):
            super().from_json(data)
            self._new_content = data["new_content"]
            self._backup_content = data.get("backup_content")

        @override
        def prepare(self):
            # self._path was initialized as relative; by now the infra
            # has prefixed it under the resolved sample path
            target: Path = self._path
            if not target.exists() or not target.is_file():
                raise FileNotFoundError(f"File {target} not found")
            self._backup_content = target.read_text(encoding="utf-8")
            target.write_text(self._new_content, encoding="utf-8")

        @override
        def cleanup(self):
            if self._backup_content is None:
                return
            target: Path = self._path
            # best-effort restore
            try:
                if target.exists() and target.is_file():
                    target.write_text(self._backup_content, encoding="utf-8")
            except OSError:
                pass
    ```

    Usage in a test:

    ```python
    import pytest
    from tests.utils.paths import TestPath

    @pytest.mark.file_operation(path=ReplaceFileContentPath("src/pkg/module.py", "print('patched')\n"))
    def test_build_respects_modified_source(assert_wheel_build, sample_project, project):
        project_path = sample_project("core_functionality/minimal")
        with project(project_path):
            assert_wheel_build(project_path)
            # ... assertions about effects of the modification ...
    ```

- **Global locks and markers** (`tests/utils/markers.py`)
  - `MarkerFile` is used to coordinate cross-process lifecycle events (e.g., venv creation, server startup, file-operation collection) with a simple reference counting protocol (`touch`/`untouch`)
  - Combined with `FileLock`, it guarantees single-producer, multi-consumer patterns across workers and safe teardown when the last consumer completes
  - By default, a `MarkerFile` starts as an empty text file on first creation, then persists JSON content on `touch()`. It can carry arbitrary, JSON-serializable metadata via the `extra` field
  - Example:

    ```python
    from pathlib import Path
    from tests.utils.markers import MarkerFile

    path = Path("/tmp") / ".server_running"

    # Attach arbitrary metadata (stored as JSON)
    marker = MarkerFile(path, extra={"port": 8000, "purpose": "http-server"})

    # Create or update marker; increments internal counter and writes JSON
    marker.touch()

    # Read back metadata later (the 'counter' field is stripped from read())
    info = marker.read()
    assert info == {"port": 8000, "purpose": "http-server"}

    # Decrement; when the last consumer calls untouch(), the file is removed
    marker.untouch()
    ```

  - FileLock pattern example (one-time init with shared usage):

    ```python
    import shutil
    from pathlib import Path
    from filelock import FileLock
    from tests.utils.markers import MarkerFile

    resource_dir = Path("/tmp/my-shared-resource")
    locks_dir = resource_dir.parent
    lock = FileLock(str(locks_dir / ".my-shared-resource.lock"))

    producer = None

    with lock:
        marker = MarkerFile(resource_dir / ".initialized", extra={"purpose": "example"})
        if not marker.exists():
            # One-time initialization guarded by the lock
            shutil.rmtree(resource_dir, ignore_errors=True)
            resource_dir.mkdir(parents=True, exist_ok=True)
            # Others processing...
            producer = ...
        else:
            # Already initialized; read metadata if needed
            info = marker.read()  # e.g., {"purpose": "example"}
            # ... optionally act on existing metadata ...
        # Reference-count this session/test as a consumer
        marker.touch()

    try:
        # Use the resource concurrently from multiple workers/tests
        # ... test logic ...
        yield
    finally:
        # Decrement and cleanup when last consumer finishes
        with lock:
            if marker.untouch(wait=False):
                shutil.rmtree(resource_dir, ignore_errors=True)
    ```
    **Variant using wait=True (cooperative teardown):** This approach blocks until all other consumers have called `untouch()`, then removes the marker file and returns `True` for the last caller. You can pass a timeout in seconds to prevent indefinite blocking.
    ```python
        if marker.untouch(wait=producer is not None):
            shutil.rmtree(resource_dir, ignore_errors=True)
    ```

- **Logging and diagnostics** (`conftests/logger.py`)
  - Consistent, session-wide logging with `root_logger`, plus helpers `log_info` and `log_info_section` for structured output around build steps and assertions

- **PyInstaller config isolation**
  - `pyinstaller_path` fixture sets `PYINSTALLER_CONFIG_DIR` per test function to avoid cross-test contamination when PyInstaller writes cache/config files

- **Pytest markers** (registered in `tests/conftest.py`)
  - `prevent_venv_self_build`: conditionally skip building Poexy-Core into the session venv
  - `use_http_server`: enable and prepare the session HTTP server
  - `use_git_server`: enable and prepare the session Git server
  - `file_operation`: declare a filesystem manipulation to run for the test

  Basic marker usage examples:

  ```python
  import pytest

  # Enable the session HTTP server for this test
  @pytest.mark.use_http_server
  def test_with_http_server(sample_project, project, assert_wheel_build):
      project_path = sample_project("dependencies/url/simple")
      with project(project_path):
          assert_wheel_build(project_path)

  # Enable the session Git server for this test
  @pytest.mark.use_git_server
  def test_with_git_server(sample_project, project, assert_sdist_build):
      project_path = sample_project("dependencies/git/simple")
      with project(project_path):
          assert_sdist_build(project_path)

  # Apply a simple file operation before the test body and clean it after
  from tests.utils.paths import InaccessiblePath

  @pytest.mark.file_operation(path=InaccessiblePath("src/pkg/data.txt"))
  def test_with_file_operation(sample_project, project, assert_wheel_build):
      project_path = sample_project("edge_cases/inaccessible_file")
      with project(project_path):
          assert_wheel_build(project_path)

  # Prevent building poexy-core into the session venv during venv bootstrap
  # Useful when you only need dependencies installed for faster setup
  @pytest.mark.prevent_venv_self_build
  def test_without_self_build(sample_project, project, assert_sdist_build):
      project_path = sample_project("core_functionality/minimal")
      with project(project_path):
          assert_sdist_build(project_path)
  ```

  > Info
  >
  > - `prevent_venv_self_build` is a session-wide opt-out that only applies when **all collected tests** in the session are marked with it. If even one collected test is not marked, Poexy-Core will be built/installed into the session virtual environment.
  > - A similar session-level logic is applied to `use_http_server` and `use_git_server`: servers are started only if **at least one collected test** has the corresponding marker. If no test is marked, the servers are not started.
  > - `file_operation`: tests that depend on the same sample path are serialized—executed sequentially—to avoid contention on shared sample resources, while allowing other tests to run in parallel.

- **Typical end-to-end test flow**
  1. Resolve sample path via `sample_project("<name>")`
  2. Enter `with project(project_path): ...`
  3. Build using `assert_wheel_build` and/or `assert_sdist_build`
  4. Validate manifests and archive contents using assertion fixtures
  5. Optionally execute installed binary via `execute_binary` and assert output

#### Path assertion markers (`AssertPath`)

The test framework provides a sophisticated path assertion system with markers to specify file types, destinations, and package targets. This allows precise control over which files should be included or excluded from builds.

##### Marker syntax

Markers are embedded directly in path strings using colon notation:
```python
# Basic syntax: [exclude_mark] [target_mark] PATH [kind_marks]
expected_files = [
    "__init__.py",                # Default: included in all packages (purelib)
    "whl:my_script:bin",          # Binary script: wheel package only
    "tar:config.json:plat:data",  # Data file: source distribution only
    "!:temp/debug.log",           # Excluded from all packages
]
```

##### Marker types

**Exclude marker** `[!:]`
- `!:` - Exclude path from all packages

> Must be at the beginning of the path

**Target markers** `[tar: | whl: | all:]`
- `tar:` - Assert only in source distribution (tar.gz)
- `whl:` - Assert only in wheel package
- `all:` - Assert in both packages (default behavior)

> Must be at the beginning of the path (after exclude marker)

**Kind markers** `[:file | :ln | :plat | :data | :cfg | :cache | :purelib | :platlib | :bin]`
- **File types:**
  - `:file` - Regular file (default)
  - `:ln` - Symbolic link
- **Platform types:**
  - `:plat`   - Platform-specific content
  - `:data`   - Platform-specific data subdirectory
  - `:cfg`    - Platform-specific confgiration subdirectory  
  - `:cache`  - Paltform-specific cache subdirectory
- **Destinations:**
  - `:purelib` - Pure Python library directory (default). Will be resolved to source package directory for in Tar context
  - `:platlib` - Platform-specific library directory. Not used in Tar context
  - `:bin` - Binary/script directory

> Must be at the end of the path

##### Usage examples

```python
from tests.utils.asserts import AssertPaths

# Define expected files with markers
expected_files = [
    # Regular Python files (default: all packages, purelib)
    "__init__.py",
    "core.py",
    
    # Platform-specific files
    "native.so:plat:platlib",
    
    # Binary scripts (wheel only)
    "whl:my_script:bin",
    "whl:helper.sh:bin",
    
    # Data files (source distribution only)  
    "tar:templates/config.json:plat:data",
    "tar:docs/README.txt:plat:data",
    
    # Symbolic links
    "tar:lib/symlink_target:ln",
    
    # Excluded files
    "!:temp/build.log",
    "!:cache/debug.cache",
]

# Create assertion helper
paths = AssertPaths(expected_files)

# Filter by package type
wheel_files = paths.included(target=AssertPathPackageTarget.Wheel)
tar_files = paths.included(target=AssertPathPackageTarget.Tar)

# Filter by file kind
binary_files = paths.binaries()
symlinks = paths.links()
excluded = paths.excluded()

# Use in assertions
assert_zip_file.assert_has_files(wheel_files)
assert_tar_file.assert_has_files(tar_files)
```

##### Advanced features

**Variable expansion** for binary paths:
```python
# Use $BINARY placeholder for dynamic binary names
expected_files = ["whl:$BINARY:bin"] # resolved from package name
paths = AssertPaths(expected_files)
paths.expand("my_script", AssertPathKind.Binary)
# Results in: "bin/my_script"
```

**Base path remapping** for nested structures:
```python
paths = AssertPaths(["subdir/file.py", "subdir/module.py"])
paths.remap_base_path(Path("src"))
# Results in: "my_package/subdir/file.py", "my_package/subdir/module.py"
```

#### Parallelization and shared resources (details)

The test suite is optimized for parallel execution (e.g., with `pytest-xdist`). It relies on an explicit coordination model to minimize total runtime while preserving deterministic behavior and strict test isolation:

- Goals: avoid redundant heavy work (e.g., creating venvs/servers), maximize resource reuse across workers, and keep tests isolated and reproducible.
- Coordination primitives:
  - `FileLock`: guarantees mutual exclusion for one-time initialization/teardown across workers.
  - `MarkerFile`: reference-counted lifecycle: `touch()` increments and persists JSON metadata; `untouch(wait=...)` decrements and removes the file on the last consumer.
  - Session markers (`prevent_venv_self_build`, `use_http_server`, `use_git_server`) drive whether session-scoped resources are created at all.
- Patterns used:
  - Single-producer / multi-consumer for session resources (venv archive, HTTP/Git servers): create once under a lock; each consumer calls `touch()`; last `untouch()` performs teardown.
  - Per-sample serialization for destructive file operations to ensure correctness under concurrency.
- Do:
  - Guard any shared resource init/teardown with `FileLock` + `MarkerFile` and keep lock scopes minimal.
  - Keep operations idempotent, use `try/finally` to guarantee `untouch()`/cleanup.
  - Prefer existing fixtures (session venv, servers) instead of ad-hoc resources in tests.
  - Store metadata in `MarkerFile.extra` to communicate state across workers when needed.
- Don’t:
  - Mutate `tests/samples/` outside declared `@pytest.mark.file_operation` paths.
  - Start ad-hoc servers or bind fixed ports outside the provided server fixtures.
  - Write to global paths outside test tmp roots.
- Extending infra:
  - For any new shared resource, replicate the lock/marker pattern (one-time init under lock; `marker.touch()` per consumer; `marker.untouch(wait=...)` on teardown) and document the chosen marker name and metadata.
- Performance notes:
  - Heavy tasks (venv creation, server bootstrap) occur once per session when needed. If all collected tests opt-out via `prevent_venv_self_build`, Poexy-Core isn’t installed into the session venv; otherwise it is. Servers start only if at least one collected test requires them.

<a id="project-structure"></a>
## 📁 Project Structure

```
poexy-core/
├── poexy_core/
│  ├── api.py                    # PEP 517/518 build backend interface
│  ├── builders/                 # Package builders (wheel, sdist, binary)
│  │  ├── builder.py             # Base builder implementation
│  │  ├── wheel.py               # Wheel package builder
│  │  ├── sdist.py               # Source distribution builder
│  │  ├── binary.py              # Binary executable builder
│  │  ├── editable.py            # Editable wheel builder
│  │  ├── types.py               # Builder type definitions
│  │  └── hooks/                 # Build hooks for file processing
│  │      ├── hook.py            # Base hook builder class
│  │      ├── readme.py          # README file processing hook
│  │      ├── license.py         # License file processing hook
│  │      ├── include_files.py   # File inclusion/exclusion hook
│  │      ├── package_files.py   # Package file processing hook
│  │      └── binary.py          # Binary-specific file processing hook
│  ├── packages/                 # Package format definitions and file management
│  │  ├── package.py             # Package format definitions
│  │  ├── files.py               # File management utilities
│  │  ├── inclusions.py          # File inclusion/exclusion logic
│  │  ├── validators.py          # Package validation
│  │  └── format.py              # Format type definitions
│  ├── pyproject/                # pyproject.toml parsing and validation
│  │  ├── toml.py                # TOML configuration parser
│  │  ├── types.py               # Configuration type definitions
│  │  ├── exceptions.py          # Configuration exceptions
│  │  └── tables/                # Pydantic table definitions
│  │      ├── package.py         # Package table definition
│  │      ├── poexy.py           # Main poexy table definition
│  │      ├── license.py         # License table definition
│  │      └── readme.py          # README table definition
│  ├── pyinstaller/              # PyInstaller integration
│  │  ├── builder.py             # PyInstaller builder implementation
│  │  ├── argument_builder.py    # PyInstaller argument builder
│  │  ├── venv.py               # Virtual environment management
│  │  └── types.py              # PyInstaller type definitions
│  ├── metadata/                 # Package metadata handling
│  │  ├── builder.py             # Metadata builder
│  │  └── fields.py              # Metadata field definitions
│  ├── manifest/                 # File manifest management
│  │  ├── manifest.py            # Manifest implementation
│  │  ├── parser.py              # Manifest parser
│  │  └── types.py               # Manifest type definitions
│  └── utils/                    # Utility functions
│     ├── build.py               # Build utilities
│     ├── pip.py                 # Pip utilities
│     ├── venv.py                # Virtual environment utilities
│     ├── python_impl.py         # Python implementation utilities
│     └── subprocess_rt.py       # Subprocess utilities
├── tests/                       # Comprehensive test suite
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

<a id="troubleshooting"></a>
## 🔧 Troubleshooting

### Common Issues

#### 1. PyInstaller Build Fails

```bash
# Error: Module not found during binary build
```

**Solutions:**
- Ensure all dependencies are properly declared in `pyproject.toml`
- Check that your entry point path is correct
- Verify your source directory structure

#### 2. Missing Files in Binary

```bash
# Error: FileNotFoundError in binary executable
```

**Solutions:**
- Add missing files to `[tool.poexy.binary]` includes
- Check that data files are properly bundled
- Use absolute paths in your code for data files

#### 3. Import Errors

```bash
# Error: ModuleNotFoundError when running binary
```

**Solutions:**
- Verify package name matches directory structure
- Check `[tool.poexy.package.NAME]` configuration

#### 4. Build Backend Not Found

```bash
# Error: No module named 'poexy_core.api'
```

**Solutions:**
- Install poexy-core: `pip install poexy-core`
- Verify `build-backend = "poexy_core.api"` in `pyproject.toml`
- Check your Python environment

### Getting Help

1. Check the [test samples](tests/samples/) for working examples
2. Review the [project structure](#-project-structure) for file organization
3. Open an issue with your `pyproject.toml` and error message

<a id="faq--known-issues"></a>
## ❓ FAQ & Known Issues

### Known Limitations
- PyInstaller `onedir` mode not yet supported
- Limited PyInstaller customization options currently available

### **Compatibility & Migration**
- **Q: Will my Poetry plugins work with Poexy-Core?**  
  A: Poexy-Core is a build backend only. Poetry plugins for dependency management continue to work normally.

- **Q: Can I use poetry.lock with Poexy-Core?**  
  A: Yes! Poexy-Core respects existing poetry.lock files for dependency resolution.

### **Binaries & PyInstaller**
- **Q: Do generated binaries include all dependencies?**  
  A: Yes, PyInstaller automatically bundles all necessary dependencies into the executable.

- **Q: Can I create binaries for different platforms?**  
  A: You need to build on each target platform. Cross-compilation is not supported.

- **Q: What if my binary doesn't start?**  
  A: Check your entry point and consult the Troubleshooting section for common errors.

### **Configuration & Formats**
- **Q: Can I build only a wheel without sdist?**  
  A: Yes, use `python -m build --wheel` to build only the wheel or any revelant option in `poetry build` or `uv build` or any other build front-end tool.

- **Q: How do I include data files in my binary?**  
  A: Use the `[tool.poexy.{wheel, sdist}]` section with `includes` to specify additional files.

### **Performance & Development**
- **Q: Are builds slower than with standard Poetry?**  
  A: Wheel/sdist builds have similar performance. Binary builds take longer due to PyInstaller.

- **Q: Can I use editable installs for development?**  
  A: Yes! `pip install -e .` works normally for development.

<a id="contributing"></a>
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

<a id="license"></a>
## 📄 License

This project is licensed under the MIT License

<a id="why-choose-poexy-core"></a>
## 🎯 Why Choose Poexy-Core?

### 🔧 Important Note: What Poexy-Core Is (and Isn't)

**Poexy-Core is a build backend/system only** — it's **not a replacement** for Poetry or UV. Instead:

- ✅ **Complements existing tools:** Use with Poetry, UV, pip, or any PEP 517-compatible tool
- ✅ **Built on Poetry Core:** Reuses and extends Poetry's proven packaging infrastructure  
- ✅ **Focused scope:** Handles the "how to build" part, not dependency management or environment handling
- ✅ **Drop-in replacement:** Only replaces the `build-backend` in your `pyproject.toml`

**Use case:** When you need Poetry's packaging capabilities + binary executable generation in one unified system.

### vs Traditional Poetry
- ✅ **Extended capabilities:** Builds executables in addition to wheels/sdist
- ✅ **PEP 517 compliance:** Works with any build tool (`pip`, `poetry`, `uv`)
- ✅ **Unified workflow:** One configuration for all package types
- ✅ **Smart dependency handling:** Local dependencies are automatically excluded from built packages (sdist/wheel)
- ✅ **Enhanced metadata management:** More granular control with field-level versioning and deprecation tracking (PEP 639 compliant)
- ✅ **Rich metadata support:** Handles multiuse and multiline metadata fields seamlessly
- ✅ **Advanced file inclusion system:** More permissive and flexible inclusion rules managed through Poexy (not Poetry)

### vs PyInstaller Alone  
- ✅ **Integrated packaging:** No separate build scripts needed
- ✅ **Dependency management:** Automatic dependency resolution
- ✅ **Standard distribution:** Creates proper Python packages

### vs Other Build Backends
- ✅ **Multi-format support:** Source, wheel, and binary in one tool
- ✅ **Poetry compatibility:** Familiar configuration syntax
- ✅ **Advanced file control:** Precise inclusion/exclusion rules

<a id="acknowledgments"></a>
## 🙏 Acknowledgments

- Built on top of [Poetry Core](https://python-poetry.org/) for robust Python packaging
- Uses [PyInstaller](https://pyinstaller.org/) for reliable binary executable creation
- Leverages [Pydantic](https://pydantic.dev/) for type-safe configuration validation
- Enhanced with [Rich](https://rich.readthedocs.io/) for beautiful console output
- Integrates [VirtualEnv](https://virtualenv.pypa.io/) for environment management
- Compatible with [UV](https://docs.astral.sh/uv/) for fast Python package management
- Compliant with [PEP 517](https://peps.python.org/pep-0517/)/[518](https://peps.python.org/pep-0518/)/[639](https://peps.python.org/pep-0639/)/[660](https://peps.python.org/pep-0660/) standards

<a id="support"></a>
## 📞 Support

- 🐛 **Bug reports:** [Open an issue](https://github.com/your-repo/poexy-core/issues)
- 💬 **Questions:** [Discussions](https://github.com/your-repo/poexy-core/discussions)
- 📖 **Examples:** Check the [test samples](tests/samples/) directory
- 🤝 **Contributing:** Read our [contribution guidelines](#-contributing)
- 📚 **Documentation:** [Full documentation](link-to-docs)

---

**Happy packaging! 🎉** 