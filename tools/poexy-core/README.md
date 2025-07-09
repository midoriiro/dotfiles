# Poexy-Core

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Poexy-Core** is an advanced Python build backend based on Poetry that extends the capabilities of Python packaging. It provides a unified solution for building traditional Python packages (wheels, sdist) and standalone executable applications using PyInstaller.

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

## 📋 Requirements

- Python 3.9 or higher
- Poetry Core 2.1.0+
- Pydantic 2.11.7+
- PyInstaller 6.14.2+
- Rich 14.0.0+

## 📖 Usage

### Basic Configuration

Add Poexy-Core as your build backend in `pyproject.toml`:

```toml
[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"
```

### Standard Python Package

For a basic Python package with wheels and sdist:

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

### Binary Executable

To create a standalone executable:

```toml
[project]
name = "my-app"
version = "1.0.0"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_app]
source = "src"

[tool.poexy.wheel]
format = ["binary"]

[tool.poexy.binary]
name = "my-app"
entry_point = "src.main:app"
```

### Multi-Format Package

Create both source and binary formats:

```toml
[project]
name = "my-multi-package"
version = "1.0.0"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_multi_package]
source = "src"

[tool.poexy.wheel]
format = ["source", "binary"]

[tool.poexy.binary]
name = "my-app"
```

With this configuration, Poexy will build a wheel that contains both your Python files and a standalone binary. When the package is installed, pip will place the Python files into `site-packages` and install the binary into the `$prefix/bin/` directory.

### Advanced File Management

Control which files are included in your packages:

```toml
[project]
name = "my-package"
version = "1.0.0"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package.my_package]
source = "src"

[tool.poexy.sdist]
includes = [
    "docs",
    "examples"
]

[tool.poexy.wheel]
includes = [
    { path = "docs", destination = "share/docs" }
]
excludes = [
    "tests",
]
```

> **Note:** With the configuration below:
>
> ```toml
> [tool.poexy.wheel]
> includes = [
>     { path = "docs", destination = "share/docs" }
> ]
> ```
>
> the `docs` directory will be installed at:  
> `$prefix/share/my-package/docs`  
> where `$prefix` is the installation prefix (such as `/usr/local` or your virtual environment), and `my-package` is the value of the `name` field in your `[project]` section.
>
> **Limitation:** At this time, there is no way to include a directory so that it is placed directly alongside your package at the root of the wheel. All included files must be mapped to a subdirectory under `$prefix/`.

> **Note:** Defaults exclusions 
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

## 🔧 Configuration Options

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
entry_point = "src.main:app"  # Entry point (optional, auto-detected if not specified)
```

### SDist Configuration

```toml
[tool.poexy.sdist]
includes = []  # Additional files to include
excludes = []  # Files to exclude
```

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

## 🧪 Testing

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

### Running Tests

```bash
# Run all tests
poetry run pytest tests

# Run with coverage
poetry run pytest tests --cov=poexy_core

# Run tests in parallel
poetry run pytest tests --numprocesses=auto
```

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
│  ├── pyinstaller/              # PyInstaller integration
│  │  └── builder.py             # PyInstaller builder implementation
│  ├── metadata/                 # Package metadata handling
│  │  ├── builder.py             # Metadata builder
│  │  └── fields.py              # Metadata field definitions
│  ├── manifest/                 # File manifest management
│  │  ├── manifest.py            # Manifest implementation
│  │  ├── parser.py              # Manifest parser
│  │  └── types.py               # Manifest type definitions
│  └── utils/                    # Utility functions
│     ├── python_impl.py         # Python implementation utilities
│     └── subprocess_rt.py       # Subprocess utilities
├── tests/                       # Comprehensive test suite
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License

## 🙏 Acknowledgments

- Built on top of [Poetry](https://python-poetry.org/) for Python packaging
- Uses [PyInstaller](https://pyinstaller.org/) for binary executable creation
- Leverages [Pydantic](https://pydantic.dev/) for configuration validation
- Enhanced with [Rich](https://rich.readthedocs.io/) for beautiful console output

## 📞 Support

For questions, issues, or contributions, please open an issue on the project repository. 