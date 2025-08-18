SDIST_EXTENSIONS = {".py", ".c", ".cpp", ".h"}

WHEEL_EXTENSIONS = {
    ".py",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
}

GLOB_EXTENSIONS = {
    *SDIST_EXTENSIONS,
    *WHEEL_EXTENSIONS,
}

FORBIDDEN_DIRS = {
    "__pycache__",
    "build",
    "dist",
    ".eggs",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "venv",
}
