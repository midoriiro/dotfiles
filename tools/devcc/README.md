# DevCC (DevContainerComposer)

A CLI tool to easily compose `devcontainer.json` files. Create and customize your containerized development environments with just a few simple commands.

## Installation

```bash
# Install with Poetry
poetry install

# Or install with pip
pip install .
```

## Usage

The CLI is organized into three main commands that can be chained together:

### Global Options

- `--output, -o` : Output path for the devcontainer.json file
- `--dry-run` : Print the configuration to stdout instead of writing to file

### Workspace Configuration

```bash
# Basic workspace configuration
devcc workspace --name "My Project" --source "/path/to/source"

# Advanced workspace configuration
devcc workspace \
    --name "My Project" \
    --source "/path/to/source" \
    --target "/workspace" \
    --mount-type "bind" \
    --mount-options "consistency=cached"
```

### Expose Configuration

```bash
# Mount Docker socket
devcc expose --mount-socket

# Configure remote container host
devcc expose --container-host "ssh://user@host:22"
```

### Runtime Environment Configuration

```bash
# Basic runtime configuration
devcc runtime --username "dev" --env-var "DEBUG=true"

# Advanced runtime configuration with mounts
devcc runtime \
    --username "dev" \
    --env-var "DEBUG=true" \
    --env-var "NODE_ENV=development" \
    --mount "/home/user/.ssh:/home/dev/.ssh:ro" \
    --mount "/home/user/.gitconfig:/home/dev/.gitconfig:ro"
```

## Example Workflow

You can chain commands together to create a complete configuration:

```bash
# All in one line
devcc workspace --name "My Project" --source "/path/to/source" expose --mount-socket runtime --username "dev" --output ".devcontainer/devcontainer.json"

# Or in multiple lines
devcc workspace --name "My Project" --source "/path/to/source" \
    expose --mount-socket \
    runtime --username "dev" \
    --output ".devcontainer/devcontainer.json"
```

Each command modifies the configuration in memory, and the final command with `--output` saves the result to a file.

## Command Reference

### Workspace Command

- `--name` : Workspace name
- `--source` : Source path of the workspace volume
- `--target` : Target path in the container (default: "/workspace")
- `--mount-type` : Mount type (default: "bind")
- `--mount-options` : Mount options (default: "consistency=cached")

### Expose Command

- `--mount-socket` : Mount the Docker socket
- `--socket-path` : Path to the Docker socket (default: "/var/run/docker.sock")
- `--container-host` : Container host (ssh://, tcp://, unix://, pipe://)

### Runtime Command

- `--username` : Username for the container
- `--env-var` : Environment variables in KEY=VALUE format (can be used multiple times)
- `--mount` : Mount points in source:target[:options] format (can be used multiple times)

## Template Example

```json
{
    "name": "Template",
    "workspaceFolder": "/workspace",
    "workspaceMount": "source=/path/to/source,target=/workspace,type=bind,consistency=cached"
}
``` 