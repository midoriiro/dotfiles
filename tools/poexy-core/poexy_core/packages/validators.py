from pathlib import Path


def validate_path(field: str, value: Path) -> Path:
    if "*" in str(value):
        raise ValueError(f"{field} path '{value}' is a glob pattern")
    if value.is_absolute():
        raise ValueError(f"{field} path '{value}' is absolute")
    if not value.exists():
        raise ValueError(f"{field} path '{value}' does not exist")
    return value


def validate_destination(field: str, value: Path) -> Path:
    if "*" in str(value):
        raise ValueError(f"{field} path '{value}' is a glob pattern")
    if value.is_absolute():
        raise ValueError(f"{field} path '{value}' is absolute")
    return value
