import json
import os
poetry_projects = []
pipx_tools = 'poetry'
if '${{ env.POEXY_CORE_PROJECT_CHANGED }}' == 'true':
    poetry_projects.append({
        'path': 'tools/poexy-core',
        'pipx-tools': pipx_tools,
        'package-name': 'poexy-core',
        'dependency-groups': 'main, dev, test',
        'builds-registry-path': 'builds/',
        'builds-registry-key': 'builds-poexy-core',
        'is-single-artifact': 'true',
        'use-poexy-core': 'false',
        'use-mutex': 'false'
    })
# if '${{ env.IGNITE_PROJECT_CHANGED }}' == 'true':
#   poetry_projects.append({
#     'path': 'tools/ignite',
#     'pipx-tools': pipx_tools,
#     'package-name': 'ignite',
#     'builds-registry-path': 'builds/',
#     'builds-registry-key': 'builds-ignite',
#     'is-single-artifact': 'false',
#     'use-poexy-core': 'true',
#     'use-mutex': 'true'
#   })
matrix_data = json.dumps(poetry_projects)
print(matrix_data)
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(f"result={matrix_data}\n")
