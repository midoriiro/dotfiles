import json
import os
from typing import Dict, List
poetry_projects = []
pipx_tools = 'poetry'
supported_os = [
    'ubuntu-latest',
    # 'windows-latest',
    # 'macos-latest'
]
last_supported_python_version = '3.13'
supported_python_versions = [
    # '3.9',
    # '3.10',
    # '3.11',
    # '3.12',
    last_supported_python_version
]

def add_project(
    projects: List[Dict], 
    project: Dict,
    project_name: str,
    os: List[str], 
    python_version: List[str]
):
    project['supported-os'] = os
    project['supported-python-versions'] = python_version
    project['last-supported-python-version'] = last_supported_python_version
    projects.append({
        'name': project_name,
        'project': project
    })


poexy_core_project_changed = os.environ.get('POEXY_CORE_PROJECT_CHANGED')
ignite_project_changed = os.environ.get('IGNITE_PROJECT_CHANGED')
print(f"POEXY_CORE_PROJECT_CHANGED: {poexy_core_project_changed}")
print(f"IGNITE_PROJECT_CHANGED: {ignite_project_changed}")
if poexy_core_project_changed == 'true':
    add_project(
        poetry_projects, 
        {
            'path': 'tools/poexy-core',
            'pipx-tools': pipx_tools,
            'package-name': 'poexy-core',
            'dependency-groups': 'main, dev, test',
            'builds-registry-path': 'builds/',
            'builds-registry-key': 'builds-poexy-core',
            'is-single-artifact': 'true',
            'use-poexy-core': 'false',
            'use-mutex': 'false'
        }, 
        "Poexy Core",
        supported_os, 
        supported_python_versions
    )
# if ignite_project_changed == 'true':
#   add_project(
#         poetry_projects, 
#         {
#             'path': 'tools/ignite',
#             'pipx-tools': pipx_tools,
#             'package-name': 'ignite',
#             'dependency-groups': 'main, dev, test',
#             'builds-registry-path': 'builds/',
#             'builds-registry-key': 'builds-ignite',
#             'is-single-artifact': 'false',
#             'use-poexy-core': 'true',
#             'use-mutex': 'true'
#         }, 
#         "Ignite",
#         supported_os, 
#         supported_python_versions
#     )
matrix = poetry_projects
matrix_data = json.dumps(matrix)
print(matrix_data)
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(f"result={matrix_data}\n")
