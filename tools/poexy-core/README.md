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
    { path = "docs", destination = "share/docs" },
    { path = "config", destination = "etc" }
]
excludes = [
    "tests",          # Exclude test files
    "docs/**/*.rst",  # Exclude specific patterns
    "*.txt"           # Exclude by extension
]
```

**Result:**
- **Source distribution:** Includes docs, examples, and changelog
- **Wheel:** Installs docs to `$prefix/share/my-package/docs` and config to `$prefix/etc/my-package/`

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

### Running Tests

```bash
# Run all tests
poetry run pytest tests

# Run with coverage
poetry run pytest tests --cov=poexy_core

# Run tests in parallel
poetry run pytest tests --numprocesses=auto
```

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