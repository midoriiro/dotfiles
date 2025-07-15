import json
import os
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
utils_path = current_file_path.parent.parent
sys.path.insert(1, str(utils_path))

from utils.packages import Package, PoetryPackage

artifacts_registry_path = Path(os.getenv("ARTIFACTS_REGISTRY_PATH"))

print(f"ℹ️ Artifacts registry path: {artifacts_registry_path}")

packages_file_path = artifacts_registry_path / "packages.json"

if not packages_file_path.exists():
    print(f"❌ Packages file does not exist: {packages_file_path}")
    exit(1)

with open(packages_file_path, "r") as f:
    packages = json.load(f)

for package in packages:
    package["assets_path"] = str(Path(package["assets"][0]).parent)
    package["assets"] = json.dumps(package["assets"])
    package["pre_commands"] = json.dumps(package["pre_commands"])
    package["post_commands"] = json.dumps(package["post_commands"])

packages_data = json.dumps(packages)

with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"result={packages_data}\n")

print(f"ℹ️ Packages: {packages}")
