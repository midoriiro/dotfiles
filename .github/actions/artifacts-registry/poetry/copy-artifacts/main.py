import os
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
utils_path = current_file_path.parent.parent.parent
sys.path.insert(1, str(utils_path))

from utils.packages import PoetryPackage

project_path = Path(os.environ.get("POETRY_PROJECT_PATH"))
project_name = os.environ.get("PROJECT_NAME")
project_version = os.environ.get("PROJECT_VERSION")
artifacts_registry_path = Path(os.environ.get("ARTIFACTS_REGISTRY_PATH"))

print(f"ℹ️ Project path: {project_path}")
print(f"ℹ️ Project dist path: {project_path}/dist")
print(f"ℹ️ Project name: {project_name}")
print(f"ℹ️ Project version: {project_version}")
print(f"ℹ️ Artifacts registry path: {artifacts_registry_path}")
print(f"ℹ️ Current working directory: {Path.cwd()}")

if not project_path.exists():
    print(f"❌ Project path does not exist: {project_path}")
    exit(1)

PoetryPackage.copy_artifacts(
    artifacts_registry_path, project_path, project_name, project_version
)

print(f"✅ Artifacts copied")
