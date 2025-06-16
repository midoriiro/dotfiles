# DevCC (DevContainerComposer)

A CLI tool to easily compose `devcontainer.json` files. Create and customize your containerized development environments with just a few simple commands.

## Installation

```bash
# Install with Poetry
poetry install

# Or install with pip
pip install .
```

## Example Workflow

You can chain commands together to create a complete configuration:

```bash
# All in one line
 devcc workspace --name "My Project" --volume-name "myproject_volume" \
    expose --socket "/var/run/docker.sock:/var/run/docker.sock" \
    runtime --user "container:dev" --env "container:DEBUG=true" \
    build --container-file "./Dockerfile" --context "." --target "dev" \
    image --name "myrepo/myimage:latest" \
    network --name "my_network" \
    --output ".devcontainer/devcontainer.json"

# Or in multiple lines
devcc workspace --name "My Project" --volume-name "myproject_volume"

devcc expose --address "ssh://user@host:22"

devcc runtime --user "container:dev" --env "container:DEBUG=true" --mounts "/home/user/.ssh:/home/dev/.ssh:bind:ro"

devcc build --container-file "./Dockerfile"

devcc image --name "myrepo/myimage:latest"

devcc network --name "my_network"
```

Each line creates a fragment of the devcontainer file, and the final command with `--output` assembles and saves the complete configuration.

## Usage

The CLI is organized into several main commands that can be chained together:

### Global Options

- `--output, -o` : Output path for the devcontainer.json file
- `--dry-run` : Print the configuration to stdout instead of writing to file

### Command References

#### workspace

- `--name` : Workspace name (alphanumeric, min 3 chars)
- `--volume-name` : Workspace volume name (min 3 chars, starts with letter, alphanumeric, underscores, dashes)

#### expose

- `--socket` : Socket path in format `host_path:container_path` (both absolute paths)
- `--address` : Container host (must start with `ssh://`, `tcp://`, or `unix://`)

#### runtime

- `--user` : Container user in format `container:username` or `remote:username` (not root, min 3 chars, alphanumeric)
- `--env` : Environment variable in `container:key=value` or `remote:key=value` format (can be used multiple times)
- `--mounts` : Mount points in `source:target:type[:options]` format (can be used multiple times)

#### build

- `--container-file` : Path to the container file (required)
- `--context` : Path to the build context
- `--target` : Target build stage

#### image

- `--name` : Name of the image (`[repository/]name[:tag]`)

#### network Command

- `--name` : Name of the network