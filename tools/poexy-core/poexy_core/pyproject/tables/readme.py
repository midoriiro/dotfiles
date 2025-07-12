from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from poetry.core.packages.package import Package
from pydantic import BaseModel, Field, model_validator

from poexy_core.pyproject.types import GlobPattern

# pylint: disable=no-member


class ReadmeContentType(str, Enum):
    Markdown = "text/markdown"
    RestructuredText = "text/x-rst"


class Readme(BaseModel):
    file: GlobPattern = Field(
        description="The file to use as the README for the project.",
    )
    content_type: Optional[ReadmeContentType] = Field(
        description="The content type of the README file.",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError(f"Invalid readme type: {type(data)}")
        file = data.get("file", None)
        if file is None:
            raise ValueError("File is required")
        if isinstance(file, str):
            file = GlobPattern(pattern=Path(file))
        content_type = data.get("content-type", None)
        if content_type is not None:
            content_type = ReadmeContentType(content_type)
        if file.pattern.suffix == ".md":
            content_type = ReadmeContentType.Markdown
        elif file.pattern.suffix == ".rst":
            content_type = ReadmeContentType.RestructuredText
        else:
            raise ValueError(
                "Cannot determine content type from file extension: "
                f"{file.pattern.suffix}"
            )
        data["file"] = file
        data["content_type"] = content_type
        return data

    @staticmethod
    def from_project_config(config: Dict[str, Any]) -> Optional["Readme"]:
        project = config.get("project", None)
        assert isinstance(project, dict)
        readme = project.get("readme", None)
        if readme is None:
            return None
        if isinstance(readme, str):
            return Readme(file=GlobPattern(pattern=Path(readme)), content_type=None)
        elif isinstance(readme, dict):
            return Readme(**readme)
        else:
            raise ValueError(f"Invalid readme type: {type(readme)}")

    def transform_poetry_package(self, package: Package):
        package.readmes = ()
        readme_content = self.file.pattern.read_text(encoding="utf-8")
        package.readme_content = readme_content
        if self.content_type is None:
            raise ValueError("Content type is required")
        package.readme_content_type = self.content_type.value
