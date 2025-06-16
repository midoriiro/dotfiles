import json
from enum import Enum
from typing import Dict, List, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class MountType(str, Enum):
    BIND = "bind"
    VOLUME = "volume"


class MountPoint(BaseModel):
    source: str = Field(..., description="Source path for the mount point")
    target: str = Field(..., description="Target path in the container")
    type: MountType = Field(..., description="Type of mount (bind or volume)")
    options: Optional[str] = Field(None, description="Additional mount options")

    def __str__(self) -> str:
        options_str = f",options={self.options}" if self.options else ""
        return f"source={self.source},target={self.target},type={self.type.value}{options_str}"


class Env(BaseModel):
    key: str = Field(..., description="Environment variable key")
    value: str = Field(..., description="Environment variable value")


class ConnectionURL(BaseModel):
    """A model to handle connection URLs for different schemes."""
    scheme: Literal["ssh://", "tcp://", "unix://"] = Field(..., description="Connection scheme")
    host: Optional[str] = Field(None, description="Hostname or IP address")
    port: Optional[int] = Field(None, description="Port number")
    path: Optional[str] = Field(None, description="Path for unix:// scheme")

    @classmethod
    def from_string(cls, url: str) -> "ConnectionURL":
        """Create a ConnectionURL instance from a string URL."""
        try:
            parsed = urlparse(url)
            parsed.port # trigger property access to raise ValueError if port is not an integer
        except ValueError as e:
            if "Port out of range 0-65535" in str(e):
                raise ValueError("port must be between 1 and 65535")
            if "Port could not be cast to integer value" in str(e):
                raise ValueError("port must be an integer between 1 and 65535")
        
        scheme = f"{parsed.scheme}://"
        
        if scheme in ["ssh://", "tcp://"]:
            if not parsed.hostname or not parsed.hostname.strip():
                raise ValueError("host is required for ssh:// and tcp:// schemes")
            if parsed.port is None:
                raise ValueError("port is required for ssh:// and tcp:// schemes")
            if parsed.port < 1 or parsed.port > 65535:
                raise ValueError("port must be between 1 and 65535")
            if parsed.path:
                raise ValueError("path should not be set for ssh:// and tcp:// schemes")
            return cls(
                scheme=scheme,
                host=parsed.hostname,
                port=parsed.port,
            )
        elif scheme == "unix://":
            if parsed.hostname or parsed.port:
                raise ValueError("host and port should not be set for unix:// scheme")
            if not parsed.path:
                raise ValueError("path is required for unix:// scheme")
            return cls(
                scheme=scheme,
                path=parsed.path,
            )
        else:
            raise ValueError(f"Invalid URL scheme: {scheme}")

    
    def to_string(self) -> str:
        """Convert the ConnectionURL instance to a string URL."""
        if self.scheme in ["ssh://", "tcp://"]:
            if not self.host:
                raise ValueError("host is required for ssh:// and tcp:// schemes")
            if self.port is None:
                raise ValueError("port is required for ssh:// and tcp:// schemes")
            if not self.host.strip():
                raise ValueError("host cannot be empty")
            if self.port < 1 or self.port > 65535:
                raise ValueError("port must be between 1 and 65535")
            return f"{self.scheme}{self.host}:{self.port}"
        else:  # unix://
            if self.host or self.port:
                raise ValueError("host and port should not be set for unix:// scheme")
            if not self.path:
                raise ValueError("path is required for unix:// scheme")
            return f"{self.scheme}{self.path}"
        
    def __str__(self) -> str:
        return self.to_string()


class Feature(BaseModel):
    """Base model for all features."""
    
    def compose(self) -> Dict:
        """Compose the feature into a dictionary according to the devcontainer spec."""
        raise NotImplementedError("Subclasses must implement this method")


class ExposeFeature(Feature):
    """Configuration for container-out-container settings."""
    socket: Optional[MountPoint] = Field(None, description="Socket mount point")
    address: Optional[ConnectionURL] = Field(None, description="Container connection URL")
    
    def compose(self) -> Dict:
        """Compose the ExposeFeature into a dictionary according to the devcontainer spec."""
        composed = {}
        # Transform data as needed for devcontainer spec
        if self.socket:
            composed['mounts'] = [str(self.socket)]
        if self.address:
            composed['containerEnv'] = {'CONTAINER_HOST': str(self.address)}
        return composed


class RuntimeFeature(Feature):
    """Configuration for container runtime settings."""
    remoteUser: Optional[str] = Field(None, description="Remote user")
    containerUser: Optional[str] = Field(None, description="Container user")
    containerEnv: Optional[List[Env]] = Field(None, description="Container environment variables")
    remoteEnv: Optional[List[Env]] = Field(None, description="Remote environment variables")
    mounts: Optional[List[MountPoint]] = Field(None, description="Mount points")
    
    def compose(self) -> Dict:
        """Compose the RuntimeFeature into a dictionary according to the devcontainer spec."""
        composed = {}
        # Transform data as needed for devcontainer spec
        if self.remoteUser:
            composed['remoteUser'] = self.remoteUser
        if self.containerUser:
            composed['containerUser'] = self.containerUser
        if self.containerEnv:
            composed['containerEnv'] = {env.key: env.value for env in self.containerEnv}
        if self.remoteEnv:
            composed['remoteEnv'] = {env.key: env.value for env in self.remoteEnv}
        if self.mounts:
            composed['mounts'] = [str(mount) for mount in self.mounts]
        return composed


class WorkspaceFeature(Feature):
    """Configuration for workspace settings."""
    name: Optional[str] = Field(None, description="Workspace name")
    workspaceMount: Optional[MountPoint] = Field(None, description="Workspace mount point")
    
    def compose(self) -> Dict:
        """Compose the WorkspaceFeature into a dictionary according to the devcontainer spec."""
        composed = {}
        # Transform data as needed for devcontainer spec
        if self.name:
            composed['name'] = self.name
        if self.workspaceMount:
            composed['workspaceMount'] = str(self.workspaceMount)
        return composed


class ContainerImageFeature(Feature):
    """Configuration for container image settings."""
    name: Optional[str] = Field(None, description="Name of the container image")

    def compose(self) -> Dict:
        """Compose the ContainerImageFeature into a dictionary according to the devcontainer spec."""
        composed = {
            'image': self.name
        }
        return composed

    def has_valid_fields(self) -> bool:
        """Check if at least one field is not None."""
        return self.name is not None


class ContainerBuildFeature(Feature):
    """Configuration for container build settings."""
    container_file: Optional[str] = Field(None, description="Path to the container file")
    context: Optional[str] = Field(None, description="Path to the build context")
    target: Optional[str] = Field(None, description="Target build stage")

    def compose(self) -> Dict:
        """Compose the ContainerBuildFeature into a dictionary according to the devcontainer spec."""
        composed = {
            "build": {}
        }
        if self.container_file:
            composed['build']['dockerFile'] = self.container_file
        if self.context:
            composed['build']['context'] = self.context
        if self.target:
            composed['build']['target'] = self.target
        return composed

    def has_valid_fields(self) -> bool:
        """Check if at least one field is not None."""
        return any(field is not None for field in [self.container_file, self.context, self.target])

class ContainerNetworkFeature(Feature):
    """Configuration for container network settings."""
    name: Optional[str] = Field(None, description="Network name")
    
    def has_valid_fields(self) -> bool:
        """Check if the network feature has valid fields."""
        return self.name is not None and len(self.name.strip()) > 0
    
    def compose(self) -> Dict:
        """Compose the ContainerNetworkFeature into a dictionary according to the devcontainer spec."""
        composed = {}
        if self.name:
            composed['runArgs'] = [f'--network={self.name}']
        return composed