import json
import shutil
from enum import Enum
from pathlib import Path
from typing import List


class PackageType(str, Enum):
    Poetry = "poetry"


class Package:
    def __init__(self, type: PackageType, name: str, version: str, assets: List[Path]):
        self.type = type
        self.name = name
        self.version = version
        self.assets = assets
        self.commit_message = f"chore(release): bump '{name}' version to '{version}'"
        self.pre_commands = []
        self.post_commands = []

    def __eq__(self, other):
        return (
            self.type == other.type
            and self.name == other.name
            and self.version == other.version
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_dict(data: dict) -> "Package":
        if data["type"] == PackageType.Poetry.value:
            return PoetryPackage.from_dict(data)
        else:
            raise ValueError(f"Unknown package type: {data['type']}")

    def to_dict(self):
        return {
            "type": self.type.value,
            "name": self.name,
            "version": self.version,
            "assets": [str(asset) for asset in self.assets],
            "commit_message": self.commit_message,
            "pre_commands": self.pre_commands,
            "post_commands": self.post_commands,
        }


class PoetryPackage(Package):
    def __init__(self, path: Path, name: str, version: str, assets: List[Path]):
        super().__init__(PackageType.Poetry, name, version, assets)
        self.path = path
        asset_base_path = self.assets[0].parent
        self.pre_commands = [
            # f"cd {asset_base_path}",
            # "twine check --strict *.tar.gz *.whl",
            f"cd {self.path}",
            f"poetry version -- {self.version}",
            f"poetry publish --dry-run --dist-dir {self.assets[0].parent}",
            "git add pyproject.toml",
            f"git commit -m '{self.commit_message}'",
        ]
        self.post_commands = [
            f"cd {self.path}",
            f"poetry version -- {self.version}",
            f"poetry publish --dist-dir {self.assets[0].parent}",
            "git add pyproject.toml",
            f"git commit -m '{self.commit_message}'",
        ]

    def __eq__(self, other):
        return super().__eq__(other) and self.path == other.path

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_dict(self):
        data = super().to_dict()
        data["path"] = str(self.path)
        return data

    @staticmethod
    def from_dict(data: dict) -> "PoetryPackage":
        package = PoetryPackage(
            Path(data["path"]),
            data["name"],
            data["version"],
            [Path(asset) for asset in data["assets"]],
        )
        package.commit_message = data["commit_message"]
        package.pre_commands = data["pre_commands"]
        package.post_commands = data["post_commands"]
        return package

    @staticmethod
    def copy_artifacts(
        destination_path: Path,
        project_path: Path,
        project_name: str,
        project_version: str,
    ):
        dist_path = project_path / "dist"

        if not dist_path.exists():
            print(f"❌ Dist path does not exist: {dist_path}")
            exit(1)

        if not destination_path.exists():
            print(f"❌ Artifacts registry path does not exist: {destination_path}")
            exit(1)

        files = [path for path in dist_path.iterdir() if path.is_file()]

        wheel_archive_path = None
        source_archive_path = None

        for file in files:
            if file.name.endswith(".whl"):
                wheel_archive_path = file
            elif file.name.endswith(".tar.gz"):
                source_archive_path = file

        if wheel_archive_path is None or source_archive_path is None:
            print(f"❌ No wheel or tar.gz file found in {dist_path}")
            exit(1)

        destination_path = destination_path / PackageType.Poetry
        project_destination_path = destination_path / project_name
        project_destination_path.mkdir(parents=True, exist_ok=True)

        wheel_destination_path = project_destination_path / wheel_archive_path.name
        source_destination_path = project_destination_path / source_archive_path.name

        if wheel_destination_path.exists() and not wheel_archive_path.stem.endswith(
            "py3-none-any"
        ):
            # If wheel archive already exists and it is not a universal wheel, we fail.
            print(f"❌ Wheel archive already exists: {wheel_destination_path}")
            exit(1)
        elif wheel_destination_path.exists() and wheel_archive_path.stem.endswith(
            "py3-none-any"
        ):
            # If wheel archive already exists and it is a universal wheel, we ignore it.
            print(f"⚠️ Wheel archive already exists: {wheel_destination_path}")

        if source_destination_path.exists():
            # If poetry project is built in a matrix context, we will have multiple source archives.
            # If source archive already exists, we ignore it, since they will be the same across all matrix runs.
            print(f"⚠️ Source archive already exists: {source_destination_path}")

        if not wheel_destination_path.exists():
            shutil.copy(wheel_archive_path, wheel_destination_path)
            print(f"✅ Wheel archive copied to {wheel_destination_path}")

        if not source_destination_path.exists():
            shutil.copy(source_archive_path, source_destination_path)
            print(f"✅ Source archive copied to {source_destination_path}")

        with open(project_destination_path / "package.json", "w") as f:
            project_data = {
                "path": str(project_path),
                "name": project_name,
                "version": project_version,
            }
            f.write(json.dumps(project_data, indent=2))

    @staticmethod
    def packages(from_path: Path, packages: List["Package"]) -> List["Package"]:
        poetry_packages_path = from_path / PackageType.Poetry

        for project in poetry_packages_path.iterdir():
            print(f"ℹ️ Project: {project.name}")

            for file in project.iterdir():
                if file.name == "package.json":
                    with open(file, "r") as f:
                        project_data = json.load(f)
                        continue

            assets = []

            for file in project.iterdir():
                if file.name == "package.json":
                    continue

                if file.is_file():
                    print(f"  - Asset: {file.name}")
                    assets.append(file)

            project_path = project_data["path"]
            project_name = project_data["name"]
            project_version = project_data["version"]
            print(f"ℹ️ Path: {project_path}")
            print(f"ℹ️ Name: {project_name}")
            print(f"ℹ️ Version: {project_version}")
            print(f"ℹ️ Assets: {[file.name for file in assets]}")

            package = PoetryPackage(
                Path(project_path), project_name, project_version, assets
            )

            if package not in packages:
                print(f"➕ Adding new package: {package.name} v{package.version}")
                packages.append(package)
            else:
                print(f"⏭️ Package already exists: {package.name} v{package.version}")
                packages.remove(package)
                packages.append(package)
