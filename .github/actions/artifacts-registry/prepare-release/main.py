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

if packages_file_path.exists():
    print(f"ℹ️ Packages file exists: {packages_file_path}")
    with open(packages_file_path, "r") as f:
        packages = [Package.from_dict(package) for package in json.load(f)]
else:
    print(f" Packages file does not exist: {packages_file_path}")
    packages = []

PoetryPackage.packages(artifacts_registry_path, packages)

packages_data = json.dumps(packages, indent=2, default=lambda o: o.to_dict())

print(f"ℹ️ Packages: {packages_data}")

with open(packages_file_path, "w") as f:
    f.write(packages_data)

print(f"✅ Packages written to {packages_file_path}")
