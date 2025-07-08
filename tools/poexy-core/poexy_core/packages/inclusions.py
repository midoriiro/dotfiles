from pathlib import Path
from typing import List, Optional, Union, override
from pydantic import BaseModel, Field, RootModel, model_validator

from poexy_core.packages.files import FilePattern, PackageFiles, ResolvePackageFiles
from poexy_core.packages.format import PackageFormat
from poexy_core.packages.validators import extract_path_and_glob_pattern, validate_destination, validate_path_and_glob_pattern

class Exclude(BaseModel, ResolvePackageFiles):
    path: Path = Field(
        description="Path to exclude from the built archive",
    )
    formats: Optional[List[PackageFormat]] = Field(
        default=None,
        description="List of package formats to exclude. If not specified, all formats will be excluded."
    )

    @model_validator(mode="after")
    def validate(self) -> "Exclude":
        self.path = validate_path_and_glob_pattern("path", self.path)
        return self
    
    @override
    def resolve(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        if self.formats is not None and format not in self.formats:
            return None
        path, glob_pattern = extract_path_and_glob_pattern("path", self.path)
        file_pattern = FilePattern(
            glob_pattern=glob_pattern,
            path=path
        )
        if format == PackageFormat.Source:
            destination_path = path
        else:
            destination_path = base_path
        resolved = file_pattern.resolve(destination_path)
        return resolved

class Include(BaseModel, ResolvePackageFiles):
    path: Path = Field(
        description="Path to include in the built archive"
    )
    destination: Optional[Path] = Field(
        description="Relative path to the include path in the built archive",
        default=None
    )
    formats: Optional[List[PackageFormat]] = Field(
        default=None,
        description="List of package formats to include. If not specified, all formats will be included."
    )

    @model_validator(mode="after")
    def validate(self) -> "Include":            
        if self.destination is not None:
            validate_destination("destination", self.destination)
        return self
    
    @override
    def resolve(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        if self.formats is not None and format not in self.formats:
            return None
        path, glob_pattern = extract_path_and_glob_pattern("path", self.path)
        file_pattern = FilePattern(
            glob_pattern=glob_pattern,
            path=path
        )
        if format == PackageFormat.Source:
            destination_path = path
        elif self.destination is None:
            destination_path = base_path / path
        else:
            destination_path = self.destination / base_path / path
        resolved = file_pattern.resolve(destination_path)
        return resolved

IncludesType = List[Union[str, Include]]
ExcludesType = List[Union[str, Exclude]]    

class Includes(RootModel[IncludesType], ResolvePackageFiles):
    @model_validator(mode="after")
    def validate(self) -> "Includes":
        for index, item in enumerate(self.root):
            if isinstance(item, str):
                value = validate_path_and_glob_pattern("path", Path(item))
                self.root[index] = Include(path=value)
            else:
                self.root[index] = item
        return self
    
    @override
    def resolve(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        resolved = []
        for item in self.root:
            resolved_item = item.resolve(format, base_path)
            if resolved_item is not None:
                resolved.extend(resolved_item)  
        return set(resolved)

class Excludes(RootModel[ExcludesType], ResolvePackageFiles):
    @model_validator(mode="after")
    def validate(self) -> "Excludes":
        for index, item in enumerate(self.root):
            if isinstance(item, str):
                value = validate_path_and_glob_pattern("path", Path(item))
                self.root[index] = Exclude(path=value)
            else:
                self.root[index] = item
        return self
    
    @override
    def resolve(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        resolved = []
        for item in self.root:
            resolved_item = item.resolve(format, base_path)
            if resolved_item is not None:
                resolved.extend(resolved_item)  
        return set(resolved)