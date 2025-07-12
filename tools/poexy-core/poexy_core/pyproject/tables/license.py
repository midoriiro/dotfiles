import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from poetry.core.masonry.metadata import Metadata
from pydantic import BaseModel, Field, model_validator

from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.exceptions import PyProjectError
from poexy_core.pyproject.types import GlobPattern

logger = logging.getLogger(__name__)


class License(BaseModel):
    text: Optional[str] = Field(description="License text", default=None)
    expression: Optional[str] = Field(description="License expression", default=None)
    files: Optional[List[GlobPattern]] = Field(
        description="License files", default=None
    )

    @model_validator(mode="after")
    def validate_model(self) -> "License":
        if self.text is not None and self.expression is not None:
            raise ValueError("text and expression cannot be used together")
        if self.text is not None and self.files is not None:
            raise ValueError("text and files cannot be used together")
        if self.expression is not None and self.files is not None:
            raise ValueError("expression and files cannot be used together")
        return self

    def resolve_files(self) -> Optional[List[Path]]:
        if self.files is None:
            return None
        current_working_directory = Path.cwd()
        if not (current_working_directory / "pyproject.toml").exists():
            raise PyProjectError(
                "License files must be resolved from the project root directory"
            )
        files = []
        for file in self.files:
            resolved_files = file.resolve()
            if resolved_files is not None:
                files.extend(resolved_files)
        return files

    @staticmethod
    def from_project_config(config: Dict[str, Any]) -> Optional["License"]:
        project = config.get("project", None)
        assert isinstance(project, dict)
        license_files = project.get("license-files", None)
        _license = project.get("license", None)
        if isinstance(_license, Dict) and len(_license) == 1:
            license_text = _license.get("text", None)
            if license_text is not None:
                logger.warning(
                    "Key 'text' in 'license' table is deprecated, use 'license' table "
                    "directly instead"
                )
                return License(text=license_text)
            license_file = _license.get("file", None)
            if license_file is not None:
                logger.warning(
                    "Key 'file' in 'license' table is deprecated, use 'license-files'"
                    "table instead"
                )
                return License(files=[GlobPattern(pattern=license_file)])
            raise PyProjectError("[project] section must contain a valid license table")
        if isinstance(license_files, List):
            return License(files=[GlobPattern(pattern=file) for file in license_files])
        elif isinstance(_license, str):
            return License(expression=_license)
        else:
            return None

    def transform_poetry_metadata(self, metadata: Metadata, _format: PackageFormat):
        metadata.license = None
        license_files = self.resolve_files()
        if license_files is not None:
            if _format == PackageFormat.Wheel:
                file_prefix = "licences/"
            else:
                file_prefix = ""
            setattr(
                metadata,
                "license_files",
                [f"{file_prefix}{file}" for file in license_files],
            )
        if self.text is not None:
            setattr(metadata, "license", self.text)
        if self.expression is not None:
            setattr(metadata, "license_expression", self.expression)
