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

## 📋 Requirements

- Python 3.9 or higher
- Poetry Core 2.1.0+
- Pydantic 2.11.7+
- PyInstaller 6.14.2+
- Rich 14.0.0+

## 🛠️ Installation

```bash
pip install poexy-core
```

Or add to your project dependencies:

```toml
[project]
dependencies = [
    "poexy-core>=2025.6.0"
]
```

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

[tool.poexy.package]
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

[tool.poexy.package]
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

[tool.poexy.package]
source = "src"

[tool.poexy.wheel]
format = ["source", "binary"]

[tool.poexy.binary]
name = "my-app"
```

### Advanced File Management

Control which files are included in your packages:

```toml
[project]
name = "my-package"
version = "1.0.0"

[build-system]
requires = ["poexy-core"]
build-backend = "poexy_core.api"

[tool.poexy.package]
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
    "*.pyc",
    "__pycache__"
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


## 🔧 Configuration Options

### Package Configuration

```toml
[tool.poexy.package]
source = "src"  # Source directory
```

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

### Using pip

```bash
pip install build
python -m build
```

### Using Poetry

```bash
poetry build
```

### Using build directly

```bash
python -m build --wheel
python -m build --sdist
```

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=poexy_core
```

## 📁 Project Structure

```
poexy-core/
├── poexy_core/
│   ├── api.py              # PEP 517/518 build backend interface
│   ├── builders/           # Package builders (wheel, sdist, binary)
│   ├── packages/           # Package format definitions and file management
│   ├── pyproject/          # pyproject.toml parsing and validation
│   ├── pyinstaller/        # PyInstaller integration
│   ├── metadata/           # Package metadata handling
│   ├── manifest/           # File manifest management
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
└── README.md              # This file
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