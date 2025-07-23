import json
import os
from typing import Dict, List

poetry_projects = []
pipx_tools = "poetry"
supported_os = ["ubuntu-latest", "windows-latest", "macos-latest"]
last_supported_python_version = "3.13"
supported_python_versions = [
    "3.9",
    "3.10",
    "3.11",
    "3.12",
    last_supported_python_version,
]

ref_name = os.environ.get("GITHUB_REF_NAME")


def add_project(
    projects: List[Dict],
    project: Dict,
    project_name: str,
    operating_systems: List[str],
    python_versions: List[str],
):
    if ref_name.startswith("releases/") and project_name in ref_name:
        project["has-changed"] = "true"

    project["supported-os"] = json.dumps(operating_systems)
    project["supported-python-versions"] = json.dumps(python_versions)
    project["last-supported-python-version"] = last_supported_python_version
    projects.append({"name": project_name, "inputs": project})


poexy_core_project_changed = os.environ.get("POEXY_CORE_PROJECT_CHANGED", "false")
ignite_project_changed = os.environ.get("IGNITE_PROJECT_CHANGED", "false")

print(f"POEXY_CORE_PROJECT_CHANGED: {poexy_core_project_changed}")
print(f"IGNITE_PROJECT_CHANGED: {ignite_project_changed}")

print("Adding Poexy Core project to matrix")
add_project(
    poetry_projects,
    {
        "has-changed": poexy_core_project_changed,
        "path": "tools/poexy-core",
        "pipx-tools": pipx_tools,
        "package-name": "poexy_core",
        "dependency-groups": "main, dev, test",
        "builds-registry-path": "builds/",
        "builds-registry-key": "builds-poexy-core",
        "use-poexy-core": "false",
        "code-coverage-threshold": 85,
    },
    "Poexy Core",
    ["ubuntu-latest"],
    [last_supported_python_version],
)

print("Adding Ignite project to matrix")
add_project(
    poetry_projects,
    {
        "has-changed": ignite_project_changed,
        "path": "tools/ignite",
        "pipx-tools": pipx_tools,
        "package-name": "ignite",
        "dependency-groups": "main, dev, test",
        "builds-registry-path": "builds/",
        "builds-registry-key": "builds-ignite",
        "use-poexy-core": "true",
        "code-coverage-threshold": 95,
    },
    "Ignite",
    supported_os,
    supported_python_versions,
)

matrix = {
    "projects": poetry_projects,
}

print(f"Generated matrix: {json.dumps(matrix, indent=2)}")
print(f"Number of projects: {len(poetry_projects)}")

if len(poetry_projects) == 0:
    print("WARNING: No projects were added to the matrix!")
    print("This might cause the workflow to fail.")
else:
    print("Projects added to matrix")

matrix_data = json.dumps(matrix)
print(f"Final matrix JSON: {matrix_data}")

with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
    f.write(f"result={matrix_data}\n")
    f.write(f"length={len(poetry_projects)}\n")
    f.write(f"last-supported-python-version={last_supported_python_version}\n")

print("Matrix output written to GITHUB_OUTPUT")
