import json
from pathlib import Path
from typing import Optional, Dict, List

import typer
from pydantic import BaseModel

app = typer.Typer()

# Global options
output_option = typer.Option(
    None,
    "--output", "-o",
    help="Output path for the devcontainer.json file"
)
dry_run_option = typer.Option(
    False,
    "--dry-run",
    help="Print the configuration to stdout instead of writing to file"
)

class Context:
    def __init__(self):
        self.output: Optional[Path] = None
        self.dry_run: bool = False
        self.features: Dict[str, Config] = {}

context = Context()

class Config:
    def __init__(self, data: Dict = None):
        self._data: Dict = data or {}

    def to_json(self) -> str:
        """Convert the configuration to a JSON string."""
        return json.dumps(self._data, indent=2)

    @property
    def data(self) -> Dict:
        return self._data


@app.callback()
def main(
    output: Optional[Path] = output_option,
    dry_run: bool = dry_run_option
):
    """Global options for all commands."""
    context.output = output
    context.dry_run = dry_run

@app.command()
def workspace(
    name: str = typer.Option(..., help="Workspace name"),
    source: str = typer.Option(..., help="Source path of the workspace volume"),
    target: str = typer.Option("/workspace", help="Target path in the container"),
    mount_type: str = typer.Option("bind", help="Mount type (bind, volume, etc.)"),
    mount_options: str = typer.Option("consistency=cached", help="Mount options"),
):
    """Configure workspace settings."""
    try:
        # Update workspace configuration
        workspace_config = {
            "name": name,
            "workspaceFolder": target,
            "workspaceMount": f"source={source},target={target},type={mount_type},{mount_options}"
        }
        context.features["workspace"] = Config(workspace_config)
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)

@app.command()
def coc(
    mount_socket: bool = typer.Option(False, help="Mount the Docker socket"),
    socket_path: str = typer.Option("/var/run/docker.sock", help="Path to the Docker socket"),
    container_host: Optional[str] = typer.Option(None, help="Container host (ssh://, tcp://, unix://, pipe://)"),
):
    """Configure container-out-container settings."""
    try:
        coc_config = {}
        
        # Add socket mount if requested
        if mount_socket:
            if "mounts" not in coc_config:
                coc_config["mounts"] = []
            coc_config["mounts"].append({
                "source": socket_path,
                "target": socket_path,
                "type": "bind"
            })
        
        # Add container host if specified
        if container_host:
            if "containerEnv" not in coc_config:
                coc_config["containerEnv"] = {}
            coc_config["containerEnv"]["CONTAINER_HOST"] = container_host
        
        context.features["coc"] = Config(coc_config)
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)

@app.command()
def runtime(
    username: Optional[str] = typer.Option(None, help="Username for the container"),
    env_var: List[str] = typer.Option([], help="Environment variables in KEY=VALUE format"),
    mount: List[str] = typer.Option([], help="Mount points in source:target[:options] format"),
):
    """Configure runtime environment settings."""
    try:
        runtime_config = {}
        
        # Set username if provided
        if username:
            runtime_config["remoteUser"] = username
        
        # Add environment variables
        if env_var:
            if "containerEnv" not in runtime_config:
                runtime_config["containerEnv"] = {}
            for var in env_var:
                key, value = var.split("=", 1)
                runtime_config["containerEnv"][key] = value
        
        # Add mount points
        if mount:
            if "mounts" not in runtime_config:
                runtime_config["mounts"] = []
            for m in mount:
                parts = m.split(":")
                source = parts[0]
                target = parts[1]
                options = parts[2] if len(parts) > 2 else ""
                
                mount_config = {
                    "source": source,
                    "target": target,
                    "type": "bind"
                }
                if options:
                    mount_config["options"] = options
                
                runtime_config["mounts"].append(mount_config)
        
        context.features["runtime"] = Config(runtime_config)
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 