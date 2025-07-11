from enum import Enum
import json
import os
from pathlib import Path
from typing import List

class PackageType(str, Enum):
    Poetry = "poetry"

class Package:
    def __init__(
            self,
            type: PackageType,
            name: str, 
            version: str, 
            packages: List[Path]
        ):
        self.type = type
        self.name = name
        self.version = version
        self.packages = packages
        self.commit_message = f"chore(release): bump '{name}' version to '{version}'"
        self.pre_commands = []
        self.post_commands = []

    def __dict__(self):
        return {
            "type": self.type.value,
            "name": self.name,
            "version": self.version,
            "packages": [str(package) for package in self.packages],
            "commit_message": self.commit_message,
            "pre_commands": self.pre_commands,
            "post_commands": self.post_commands
        }

class PoetryPackage(Package):
    def __init__(
            self,
            path: Path,
            name: str, 
            version: str, 
            packages: List[Path]
        ):
        super().__init__(
            PackageType.Poetry, 
            name, 
            version, 
            packages
        )
        self.path = path
        self.post_commands = [
            f"poetry version -- {self.version}",
            "git add pyproject.toml",
            f"git commit -m '{self.commit_message}'"
        ]

artifacts_registry_path = Path(os.getenv("ARTIFACTS_REGISTRY_PATH"))

print(f"ℹ️ Artifacts registry path: {artifacts_registry_path}")

packages = []

poetry_packages_path = artifacts_registry_path / PackageType.Poetry

for project in poetry_packages_path.iterdir():
    print(f"ℹ️ Project: {project.name}")
    with open(project / "info.json", "r") as f:
        project_data = json.load(f)
    for version in project.iterdir():
        print(f"ℹ️ Version: {version.name}")
        packages_files = []
        source = version / "source"
        wheel = version / "wheel"
        if version.name == 'info.json':
            continue
        for file in source.iterdir():
            if file.is_file():
                print(f"\t - Source file: {file.name}")
                packages_files.append(file)
        for file in wheel.iterdir():
            if file.is_file():
                print(f"\t - Wheel file: {file.name}")
                packages_files.append(file)
        package = PoetryPackage(
            project_data["path"],
            project.name, 
            version.name, 
            packages_files
        )
        packages.append(package)
        # We should only have one version per project: TODO check this 
        break

packages_data = json.dumps(packages, indent=2, default=str)

print(f"ℹ️ Packages: {packages_data}")

packages_file_path = artifacts_registry_path / "packages.json"

with open(packages_file_path, "w") as f:
    f.write(packages_data)

print(f"✅ Packages written to {packages_file_path}")