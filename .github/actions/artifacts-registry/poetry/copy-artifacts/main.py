import os
from pathlib import Path
import shutil

project_path = Path(os.environ.get('POETRY_PROJECT_PATH'))
project_name = os.environ.get('PROJECT_NAME')
project_version = os.environ.get('PROJECT_VERSION')
artifacts_registry_path = Path(os.environ.get('ARTIFACTS_REGISTRY_PATH'))

print(f"ℹ️ Project path: {project_path}")
print(f"ℹ️ Project dist path: {project_path}/dist")
print(f"ℹ️ Project name: {project_name}")
print(f"ℹ️ Project version: {project_version}")
print(f"ℹ️ Artifacts registry path: {artifacts_registry_path}")
print(f"ℹ️ Current working directory: {Path.cwd()}")

if not project_path.exists():
    print(f"❌ Project path does not exist: {project_path}")
    exit(1)

dist_path = project_path / 'dist'

if not dist_path.exists():
    print(f"❌ Dist path does not exist: {dist_path}")
    exit(1)

if not artifacts_registry_path.exists():
    print(f"❌ Artifacts registry path does not exist: {artifacts_registry_path}")
    exit(1)

files = [path for path in dist_path.iterdir() if path.is_file()]

wheel_archive_path = None
source_archive_path = None

for file in files:
    print(f"ℹ️ File: {file}")
    if file.suffix == '.whl':
        wheel_archive_path = file
    elif file.suffix == '.tar.gz':
        source_archive_path = file

if wheel_archive_path is None or source_archive_path is None:
    print(f"❌ No wheel or tar.gz file found in {dist_path}")
    exit(1)

destination_path = artifacts_registry_path / "poetry"
destination_path = destination_path / project_name / project_version
destination_path.mkdir(parents=True, exist_ok=True)

wheel_destination_path = destination_path / "wheel"
wheel_destination_path.mkdir(parents=True, exist_ok=True)

source_destination_path = destination_path / "source"
source_destination_path.mkdir(parents=True, exist_ok=True)

wheel_destination_path = wheel_destination_path / wheel_archive_path.name
source_destination_path = source_destination_path / source_archive_path.name

if wheel_destination_path.exists() and not wheel_archive_path.stem.endswith("py3-none-any"):
    # If wheel archive already exists and it is not a universal wheel, we fail.
    print(f"❌ Wheel archive already exists: {wheel_destination_path}")
    exit(1)
elif wheel_destination_path.exists() and wheel_archive_path.stem.endswith("py3-none-any"):
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

print(f"✅ Artifacts copied to {destination_path}")
