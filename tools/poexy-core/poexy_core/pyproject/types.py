import glob
import re
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, model_validator

from poexy_core.pyproject.exceptions import PyProjectError


class GlobPattern(BaseModel):
    pattern: Path = Field(description="Glob pattern")

    @model_validator(mode="after")
    def validate_model(self) -> "GlobPattern":
        pattern = str(self.pattern)
        if self.pattern.is_absolute():
            raise ValueError(f"Pattern {pattern} should be relative")
        if ".." in pattern:
            raise ValueError(f"Pattern {pattern} cannot contain '..'")
        if re.match(r"^[_\w\-\.\/\*\?\[\]]+$", pattern) is None:
            raise ValueError(f"Pattern '{pattern}' contains invalid characters.")
        self.pattern = Path(self.pattern.as_posix())
        return self

    def resolve(self) -> Optional[List[Path]]:
        current_working_directory = Path.cwd()
        if not (current_working_directory / "pyproject.toml").exists():
            raise PyProjectError(
                "Files must be resolved from the project root directory"
            )
        files = []
        for file in glob.glob(str(self.pattern)):
            path = Path(file).resolve()
            path = path.relative_to(current_working_directory)
            if path.is_file():
                files.append(path)
        if len(files) == 0:
            return None
        return files

    def split(self) -> Tuple[Path, Optional[Path]]:
        """
        Splits the glob pattern into a path and a glob pattern.
        """
        str_path = str(self.pattern)
        path = []
        for char in str_path:
            if char == "*":
                break
            path.append(char)
        glob_pattern = str_path[len(path) :]  # noqa: E203
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
