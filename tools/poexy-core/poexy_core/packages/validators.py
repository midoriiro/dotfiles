from pathlib import Path
from typing import Callable, Optional, Tuple

def validate_path(field: str, value: Path) -> Path:
    if "*" in str(value):
        raise ValueError(f"{field} path '{value}' is a glob pattern")
    if value.is_absolute():
        raise ValueError(f"{field} path '{value}' is absolute")
    if not value.exists():
        raise ValueError(f"{field} path '{value}' does not exist")
    return value

def validate_path_and_glob_pattern(
        field: str,
        value: Path,
        glob_pattern_filter: Optional[Callable[[str], bool]] = None
    ) -> Path:
    if value.is_absolute():
        raise ValueError(f"{field} path '{value}' is absolute")
    if glob_pattern_filter is not None and "*" in str(value) and glob_pattern_filter(str(value)):
        return value
    if glob_pattern_filter is None and "*" in str(value):
        return value
    if not value.exists():
        raise ValueError(f"{field} path '{value}' does not exist")
    return value

def validate_destination(field: str, value: Path) -> Path:
    if "*" in str(value):
        raise ValueError(f"{field} path '{value}' is a glob pattern")
    if value.is_absolute():
        raise ValueError(f"{field} path '{value}' is absolute")
    return value

def extract_path_and_glob_pattern(field: str, value: Path) -> Tuple[Path, Optional[Path]]:
    str_path = str(value)
    path = []
    for char in str_path:
        if char == "*":
            break
        path.append(char)
    glob_pattern = str_path[len(path):]
    path = Path("".join(path))
    if path.is_absolute():
        path = path.relative_to(path.parent)
    if len(glob_pattern) == 0 and path.is_file():
        glob_pattern = None
    elif len(glob_pattern) == 0 and path.is_dir():
        glob_pattern = Path("**/*")
    else:
        glob_pattern = Path(glob_pattern)
    return path, glob_pattern