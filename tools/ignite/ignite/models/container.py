import os
import pathlib
import re
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, Union, override

from pydantic import BaseModel, Field, RootModel, StringConstraints, model_validator

from ignite.mergers import merge_dicts
from ignite.models.common import Identifier, IdentifierPattern
from ignite.models.fs import AbsolutePath, RelativePath

ImageRepositoryIdentifier = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=256,
        pattern=rf"^{IdentifierPattern}({IdentifierPattern}|\.)+$",
    ),
]

ImageTagIdentifier = Annotated[
    str,
    StringConstraints(
        min_length=3, max_length=256, pattern=rf"^({IdentifierPattern}|\.|\d|\-)+$"
    ),
]

Extension = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=256,
        pattern=rf"^({IdentifierPattern}\.{IdentifierPattern})$",
    ),
]

MountOption = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=256,
    ),
]


class EnvType(str, Enum):
    REMOTE = "remote"
    CONTAINER = "container"


class Feature(BaseModel):
    """Base model for all features."""

    @classmethod
    def feature_name(cls) -> str:
        """Get the name of the feature."""
        return cls.__name__.lower()

    def compose(self) -> Dict[str, Any]:
        """Compose the feature into a dictionary according to the devcontainer spec."""
        raise NotImplementedError("Subclasses must implement this method")


class Env(Feature):
    """
    Environment variable configuration for devcontainer.

    This class represents an environment variable that can be set in either the remote
    environment (host machine) or the container environment. Environment variables
    are key-value pairs that can be used to configure the behavior of applications
    running in the development container.

    Attributes:
        key (Identifier): The environment variable name. Must be a valid identifier
            following the pattern: alphanumeric characters, hyphens, and underscores.
        value (Optional[str]): The environment variable value. If None, the variable
            will be set without a value. Must be between 1 and 256 characters if provided.
        type (Optional[EnvType]): The type of environment variable. Can be either
            'remote' (set on the host machine) or 'container' (set inside the container).
            Defaults to 'remote'.

    Examples:
        >>> # Remote environment variable with value
        >>> env = Env(key="DATABASE_URL", value="postgresql://localhost:5432/mydb", type=EnvType.REMOTE)

        >>> # Container environment variable without value
        >>> env = Env(key="DEBUG", type=EnvType.CONTAINER)

        >>> # Remote environment variable (default type)
        >>> env = Env(key="API_KEY", value="secret123")

    Validation:
        - Key must be a valid identifier (3-256 characters, alphanumeric, hyphens, underscores)
        - Value must be between 1-256 characters if provided
        - Type must be a valid EnvType enum value
    """

    key: Identifier = Field(..., description="Environment variable key")
    value: Optional[str] = Field(
        None, min_length=1, max_length=256, description="Environment variable value"
    )
    type: Optional[EnvType] = Field(
        EnvType.REMOTE, description="Environment variable type (remote or container)"
    )

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the environment variable into a dictionary according to the devcontainer spec.

        This method converts the Env object into a dictionary format that follows the
        devcontainer specification. The resulting dictionary will contain either a
        'remoteEnv' or 'containerEnv' key depending on the environment variable type.

        Returns:
            Dict[str, Any]: A dictionary containing the environment variable configuration.
                The structure depends on the type:
                - For remote environment variables: {"remoteEnv": {"key": "value"}}
                - For container environment variables: {"containerEnv": {"key": "value"}}
                - If value is None: {"remoteEnv": {"key": None}} or {"containerEnv": {"key": None}}

        Examples:
            >>> env = Env(key="DEBUG", value="true", type=EnvType.CONTAINER)
            >>> env.compose()
            {'containerEnv': {'DEBUG': 'true'}}

            >>> env = Env(key="API_KEY", type=EnvType.REMOTE)
            >>> env.compose()
            {'remoteEnv': {'API_KEY': None}}

            >>> env = Env(key="DATABASE_URL", value="postgresql://localhost:5432/mydb")
            >>> env.compose()
            {'remoteEnv': {'DATABASE_URL': 'postgresql://localhost:5432/mydb'}}
        """
        if self.value:
            composed_env = {self.key: self.value}
        else:
            composed_env = {self.key: None}
        composed = {}
        if self.type == EnvType.REMOTE:
            composed["remoteEnv"] = composed_env
        else:
            composed["containerEnv"] = composed_env
        return composed


class MountType(str, Enum):
    BIND = "bind"
    VOLUME = "volume"


class Mount(BaseModel):
    """
    Represents a mount point configuration for a container.

    A mount point defines how a directory or volume from the host system is mapped
    into the container. This can be either a bind mount (mapping a host directory)
    or a volume mount (using a named Docker volume).

    Attributes:
        source (Union[AbsolutePath, Identifier]): The source for the mount point.
            For bind mounts, this must be an absolute path on the host system.
            For volume mounts, this must be a volume name (identifier).
        target (AbsolutePath): The target path inside the container where the
            source will be mounted.
        type (MountType): The type of mount - either 'bind' for directory mapping
            or 'volume' for Docker volume mounting.
        options (Optional[List[MountOption]]): Additional mount options that can
            be applied to the mount point (e.g., read-only, noexec, etc.).

    Validation Rules:
        - For VOLUME type mounts: source must be a volume name (not an absolute path)
        - For BIND type mounts: source must be an absolute path (not a volume name)
        - Target must always be an absolute path

    Examples:
        >>> # Bind mount - mapping a host directory
        >>> mount = Mount(
        ...     source="/home/user/data",
        ...     target="/workspace/data",
        ...     type=MountType.BIND,
        ...     options=[MountOption.READ_ONLY]
        ... )

        >>> # Volume mount - using a named Docker volume
        >>> mount = Mount(
        ...     source="cache-volume",
        ...     target="/cache",
        ...     type=MountType.VOLUME
        ... )
    """

    source: Union[AbsolutePath, Identifier] = Field(
        ..., description="Source for the mount point (absolute path or volume name)"
    )
    target: AbsolutePath = Field(..., description="Target path in the container")
    type: MountType = Field(..., description="Type of mount (bind or volume)")
    options: Optional[List[MountOption]] = Field(
        None, description="Additional mount options"
    )

    @model_validator(mode="after")
    def check_source(self):
        """
        Validate that the source and target are appropriate for the mount type.

        This validator ensures that:
        - Volume mounts use volume names (not absolute paths) as sources
        - Bind mounts use absolute paths (not volume names) as sources

        Raises:
            ValueError: If the source type doesn't match the mount type requirements.

        Returns:
            self: The validated Mount instance.
        """
        is_source_identifier = re.match(rf"^{IdentifierPattern}$", self.source)
        if self.type == MountType.VOLUME and not is_source_identifier:
            raise ValueError("Source must be a volume name.")
        if self.type == MountType.BIND and is_source_identifier:
            raise ValueError("Source must be an absolute path.")
        return self

    def __str__(self) -> str:
        """
        Return a string representation of the mount configuration.

        Returns:
            str: A string in the format "source=...,target=...,type=...[,options=...]"
                 suitable for use in Docker mount specifications.

        Examples:
            >>> mount = Mount(
            ...     source="/home/user/data",
            ...     target="/workspace/data",
            ...     type=MountType.BIND,
            ...     options=[MountOption.READ_ONLY]
            ... )
            >>> str(mount)
            'source=/home/user/data,target=/workspace/data,type=bind,options=ro'
        """
        options_str = f",options={",".join(self.options)}" if self.options else ""
        return f"source={self.source},target={self.target},type={self.type.value}{options_str}"

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the mount configuration into a dictionary according to the devcontainer spec.

        This method converts the Mount object into a dictionary format that follows the
        devcontainer specification. The resulting dictionary will contain a 'mounts' key
        with a list of mount specifications in the format expected by the devcontainer
        configuration.

        Returns:
            Dict[str, Any]: A dictionary containing the mount configuration.
                The structure is: {"mounts": ["source=...,target=...,type=...[,options=...]"]}
                where the mount string follows the Docker mount specification format.

        Examples:
            >>> mount = Mount(
            ...     source="/home/user/data",
            ...     target="/workspace/data",
            ...     type=MountType.BIND,
            ...     options=[MountOption.READ_ONLY]
            ... )
            >>> mount.compose()
            {'mounts': ['source=/home/user/data,target=/workspace/data,type=bind,options=ro']}

            >>> mount = Mount(
            ...     source="cache-volume",
            ...     target="/cache",
            ...     type=MountType.VOLUME
            ... )
            >>> mount.compose()
            {'mounts': ['source=cache-volume,target=/cache,type=volume']}

            >>> mount = Mount(
            ...     source="/var/log",
            ...     target="/logs",
            ...     type=MountType.BIND
            ... )
            >>> mount.compose()
            {'mounts': ['source=/var/log,target=/logs,type=bind']}
        """
        return {"mounts": [str(self)]}


class Users(Feature):
    """
    User configuration for devcontainer runtime environment.

    This class represents the user configuration for both the remote environment (host machine)
    and the container environment. It allows specifying different users for the remote and
    container contexts, which is useful for security and permission management in development
    containers.

    The Users class ensures that the remote and container users are different to maintain
    proper separation between host and container environments. This is important for security
    and to avoid potential conflicts in user management.

    Attributes:
        remote (Identifier): The user identifier for the remote environment (host machine).
            Must be a valid identifier following the pattern: alphanumeric characters,
            hyphens, and underscores. This user will be used for operations on the host
            machine outside the container.
        container (Identifier): The user identifier for the container environment.
            Must be a valid identifier following the pattern: alphanumeric characters,
            hyphens, and underscores. This user will be used for operations inside the
            development container.

    Examples:
        >>> # Different users for remote and container
        >>> users = Users(remote="host-user", container="dev-user")
        >>> users.compose()
        {'remoteUser': 'host-user', 'containerUser': 'dev-user'}

        >>> # Using with Runtime configuration
        >>> runtime = Runtime(user=Users(remote="admin", container="developer"))
        >>> runtime.compose()
        {'remoteUser': 'admin', 'containerUser': 'developer'}

    Validation:
        - Remote and container users must be different
        - Both users must be valid identifiers (3-256 characters, alphanumeric, hyphens, underscores)
        - Both fields are required
    """

    remote: Identifier = Field(..., description="Remote user")
    container: Identifier = Field(..., description="Container user")

    @model_validator(mode="after")
    def check_users(self):
        """Check that the remote and container users are different."""
        if self.remote == self.container:
            raise ValueError("Remote and container users cannot be the same.")
        return self

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the user configuration into a dictionary according to the devcontainer spec.

        This method converts the Users object into a dictionary format that follows the
        devcontainer specification. The resulting dictionary contains the user configuration
        for both remote and container environments, which will be used by the devcontainer
        runtime to set up the appropriate user contexts.

        Returns:
            Dict[str, Any]: A dictionary containing the user configuration.
                The structure is: {"remoteUser": "remote_user_id", "containerUser": "container_user_id"}
                where both values are the identifier strings for the respective users.

        Examples:
            >>> users = Users(remote="host-user", container="dev-user")
            >>> users.compose()
            {'remoteUser': 'host-user', 'containerUser': 'dev-user'}

            >>> users = Users(remote="admin", container="developer")
            >>> users.compose()
            {'remoteUser': 'admin', 'containerUser': 'developer'}

            >>> users = Users(remote="user123", container="container-user")
            >>> users.compose()
            {'remoteUser': 'user123', 'containerUser': 'container-user'}
        """
        return {
            "remoteUser": self.remote,
            "containerUser": self.container,
        }


class Runtime(Feature):
    """
    Runtime configuration for devcontainer.

    This class represents the runtime configuration that can be applied to a development
    container. It includes user configuration, environment variables, and mount points
    that define how the container should behave and what resources it should have access to.

    The Runtime feature allows you to configure:
    - User identity (single user or separate remote/container users)
    - Environment variables (remote and/or container environment)
    - Mount points (bind mounts and volume mounts)

    Attributes:
        user (Optional[Union[Identifier, Users]]): User configuration for the container.
            Can be either a single identifier (applied to both remote and container)
            or a Users object with separate remote and container user configurations.
            If None, no user configuration is applied.
        env (Optional[List[Env]]): List of environment variables to be set in the
            container. Each Env object can specify whether the variable should be
            set in the remote environment, container environment, or both.
            If None, no environment variables are configured.
        mounts (Optional[List[Mount]]): List of mount points that define how host
            directories or volumes are mapped into the container. Can include both
            bind mounts (directory mapping) and volume mounts (Docker volumes).
            If None, no mount points are configured.

    Validation Rules:
        - At least one of user, env, or mounts must be configured
        - If env is provided, it must contain at least one environment variable
        - If mounts is provided, it must contain at least one mount point
        - User configuration follows the validation rules of the Users class
        - Environment variables follow the validation rules of the Env class
        - Mount points follow the validation rules of the Mount class

    Examples:
        >>> # Runtime with single user and environment variables
        >>> runtime = Runtime(
        ...     user="developer",
        ...     env=[Env(key="DEBUG", value="true", type=EnvType.CONTAINER)]
        ... )

        >>> # Runtime with separate users and mount points
        >>> runtime = Runtime(
        ...     user=Users(remote="host-user", container="dev-user"),
        ...     mounts=[Mount(source="/data", target="/workspace/data", type=MountType.BIND)]
        ... )

        >>> # Runtime with all configurations
        >>> runtime = Runtime(
        ...     user=Users(remote="admin", container="developer"),
        ...     env=[
        ...         Env(key="DATABASE_URL", value="postgresql://localhost:5432/mydb"),
        ...         Env(key="DEBUG", value="true", type=EnvType.CONTAINER)
        ...     ],
        ...     mounts=[
        ...         Mount(source="cache-volume", target="/cache", type=MountType.VOLUME),
        ...         Mount(source="/home/user/data", target="/workspace/data", type=MountType.BIND)
        ...     ]
        ... )
    """

    user: Optional[Union[Identifier, Users]] = Field(
        None, description="User configuration (single or remote/container split)"
    )
    env: Optional[List[Env]] = Field(None, description="List of environment variables")
    mounts: Optional[List[Mount]] = Field(None, description="List of mount points")

    @model_validator(mode="after")
    def check_at_least_one(self):
        """At least one of 'user', 'env', or 'mounts' must be present."""
        if self.env is not None and len(self.env) == 0:
            raise ValueError("At least one env variable must be set in Runtime.")
        if self.mounts is not None and len(self.mounts) == 0:
            raise ValueError("At least one mount must be set in Runtime.")
        return self

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the runtime configuration into a dictionary according to the devcontainer spec.

        This method converts the Runtime object into a dictionary format that follows the
        devcontainer specification. The resulting dictionary contains all the runtime
        configurations including user settings, environment variables, and mount points
        that will be applied to the development container.

        The composition process:
        1. User Configuration: If a user is specified, it's converted to the appropriate
           format. A single identifier becomes both remote and container user, while a
           Users object provides separate configurations.
        2. Environment Variables: All environment variables are merged into a single
           dictionary, with remoteEnv and containerEnv keys as appropriate.
        3. Mount Points: Mount objects are converted to string representations that
           follow the devcontainer mount specification.

        Returns:
            Dict[str, Any]: A dictionary containing the runtime configuration.
                The structure may include:
                - "remoteUser" and "containerUser": User configuration
                - "remoteEnv" and/or "containerEnv": Environment variables
                - "mounts": List of mount point strings

        Examples:
            >>> # Runtime with single user
            >>> runtime = Runtime(user="developer")
            >>> runtime.compose()
            {'remoteUser': 'developer', 'containerUser': 'developer'}

            >>> # Runtime with separate users and environment
            >>> runtime = Runtime(
            ...     user=Users(remote="host-user", container="dev-user"),
            ...     env=[Env(key="DEBUG", value="true", type=EnvType.CONTAINER)]
            ... )
            >>> runtime.compose()
            {
                'remoteUser': 'host-user',
                'containerUser': 'dev-user',
                'containerEnv': {'DEBUG': 'true'}
            }

            >>> # Runtime with all configurations
            >>> runtime = Runtime(
            ...     user="developer",
            ...     env=[Env(key="API_KEY", value="secret123")],
            ...     mounts=[Mount(source="/data", target="/workspace/data", type=MountType.BIND)]
            ... )
            >>> runtime.compose()
            {
                'remoteUser': 'developer',
                'containerUser': 'developer',
                'remoteEnv': {'API_KEY': 'secret123'},
                'mounts': ['/data:/workspace/data:bind']
            }
        """
        composed = {}
        if self.user:
            if isinstance(self.user, Users):
                composed.update(self.user.compose())
            else:
                composed.update(
                    Users.model_construct(
                        remote=self.user, container=self.user
                    ).compose()
                )
        if self.env:
            env_data = {}
            for env in self.env:
                merge_dicts(env_data, env.compose())
            composed.update(env_data)
        if self.mounts:
            composed["mounts"] = [str(mount) for mount in self.mounts]
        return composed


class Socket(BaseModel):
    """
    Represents a socket configuration for exposing host sockets to containers.

    This class defines a socket mapping between the host system and the container,
    allowing the container to access Unix domain sockets or named pipes from the
    host machine. The socket is exposed as a bind mount, making it available
    inside the container at the specified target path.

    Attributes:
        host (AbsolutePath): The absolute path to the socket on the host system.
            This must be a valid absolute path pointing to an existing socket file
            or named pipe on the host machine.
        container (AbsolutePath): The absolute path where the socket will be
            mounted inside the container. This defines the location where the
            container can access the host socket.

    Validation Rules:
        - Both host and container paths must be absolute paths
        - Host path must point to an existing socket on the host system
        - Container path must be a valid absolute path within the container

    Examples:
        >>> # Expose Docker socket from host to container
        >>> socket = Socket(
        ...     host="/var/run/docker.sock",
        ...     container="/var/run/docker.sock"
        ... )
        >>> str(socket)
        'source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind'

        >>> # Expose custom application socket
        >>> socket = Socket(
        ...     host="/tmp/myapp.sock",
        ...     container="/workspace/myapp.sock"
        ... )
        >>> str(socket)
        'source=/tmp/myapp.sock,target=/workspace/myapp.sock,type=bind'

    Usage:
        The Socket class is typically used as part of the Expose feature to
        provide containers with access to host system sockets, enabling
        communication with services running on the host machine.
    """

    host: AbsolutePath = Field(..., description="Host socket path (absolute path)")
    container: AbsolutePath = Field(
        ..., description="Container socket path (absolute path)"
    )

    def __str__(self) -> str:
        """
        Convert the socket configuration to a mount string representation.

        This method creates a Mount object with the socket paths and returns
        its string representation, which follows the format used by container
        runtimes for bind mounts.

        Returns:
            str: A string representation of the socket mount in the format
                'source=<host_path>,target=<container_path>,type=bind'

        Examples:
            >>> socket = Socket(host="/var/run/docker.sock", container="/var/run/docker.sock")
            >>> str(socket)
            'source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind'

            >>> socket = Socket(host="/tmp/app.sock", container="/workspace/app.sock")
            >>> str(socket)
            'source=/tmp/app.sock,target=/workspace/app.sock,type=bind'
        """
        mount = Mount(source=self.host, target=self.container, type=MountType.BIND)
        return str(mount)


class URLScheme(str, Enum):
    SSH = "ssh"
    TCP = "tcp"


class URL(BaseModel):
    """
    URL configuration for network connections in devcontainer.

    This class represents a URL configuration that can be used to specify network
    connections for the devcontainer. It supports different URL schemes and can
    include optional port specifications for network communication.

    The URL class is designed to work with the Expose feature to provide containers
    with network connectivity to external services or hosts. It follows standard
    URL formatting conventions and validates the components according to network
    standards.

    Attributes:
        scheme (URLScheme): The URL scheme that defines the protocol for the connection.
            Must be one of the supported schemes (SSH, TCP). This determines how
            the connection will be established and what protocol will be used.
        host (str): The hostname or IP address for the connection. Must be a non-empty
            string between 1 and 256 characters. Can be a domain name, IP address,
            or any valid network identifier.
        port (Optional[int]): The port number for the connection. Optional field that
            must be between 1 and 65535 if specified. If not provided, the default
            port for the scheme will be used.

    Validation Rules:
        - scheme must be a valid URLScheme enum value
        - host must be a non-empty string between 1 and 256 characters
        - port must be between 1 and 65535 if specified
        - At least one of host or port must be provided

    Examples:
        >>> # SSH connection to a remote host
        >>> url = URL(scheme=URLScheme.SSH, host="example.com", port=22)
        >>> str(url)
        'ssh://example.com:22'

        >>> # TCP connection without explicit port
        >>> url = URL(scheme=URLScheme.TCP, host="192.168.1.100")
        >>> str(url)
        'tcp://192.168.1.100'

        >>> # SSH connection with default port
        >>> url = URL(scheme=URLScheme.SSH, host="git.example.com")
        >>> str(url)
        'ssh://git.example.com'

    Usage:
        The URL class is typically used as part of the Expose feature to specify
        network connections for containers. It provides a standardized way to
        define connection endpoints that can be used for various network protocols
        and services.
    """

    scheme: URLScheme = Field(..., description="Scheme of the URL")
    host: str = Field(
        ..., min_length=1, max_length=256, description="Hostname or IP address"
    )
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port number")

    def __str__(self) -> str:
        """
        Convert the URL configuration to a string representation.

        This method creates a standard URL string from the URL components.
        The format follows the standard URL specification: scheme://host[:port].
        If no port is specified, the port component is omitted from the string.

        Returns:
            str: A string representation of the URL in the format
                'scheme://host' or 'scheme://host:port' if a port is specified.

        Examples:
            >>> url = URL(scheme=URLScheme.SSH, host="example.com", port=22)
            >>> str(url)
            'ssh://example.com:22'

            >>> url = URL(scheme=URLScheme.TCP, host="localhost", port=8080)
            >>> str(url)
            'tcp://localhost:8080'

            >>> url = URL(scheme=URLScheme.SSH, host="git.example.com")
            >>> str(url)
            'ssh://git.example.com'
        """
        if self.port:
            return f"{self.scheme.value}://{self.host}:{self.port}"
        else:
            return f"{self.scheme.value}://{self.host}"


class Expose(Feature):
    """
    Expose feature for configuring container network access.

    This feature allows exposing container services through either Unix socket
    mounting or network address configuration. It supports two mutually exclusive
    modes of operation:

    1. **Socket Mode**: Mounts a Unix socket from the host into the container,
       enabling direct socket-based communication between the host and container.
       This is typically used for Docker socket access or other Unix domain
       socket services.

    2. **Address Mode**: Configures a network address for container connectivity,
       setting the CONTAINER_HOST environment variable with the specified URL.
       This enables network-based communication with the container.

    The feature enforces that exactly one of these modes must be configured
    (XOR constraint) to ensure clear and unambiguous network configuration.

    Attributes:
        socket (Optional[Socket]): Unix socket path configuration for socket-based
            communication. When specified, the socket is mounted into the container
            using the devcontainer mounts configuration.
        address (Optional[URL]): Network URL configuration for network-based
            communication. When specified, sets the CONTAINER_HOST environment
            variable with the URL string representation.

    Validation:
        - Exactly one of 'socket' or 'address' must be present (XOR constraint)
        - Both attributes cannot be None or both cannot be set simultaneously

    Examples:
        >>> # Socket-based exposure
        >>> expose = Expose(socket=Socket(path="/var/run/docker.sock"))
        >>> expose.compose()
        {'mounts': ['/var/run/docker.sock']}

        >>> # Network-based exposure
        >>> url = URL(scheme=URLScheme.SSH, host="localhost", port=2222)
        >>> expose = Expose(address=url)
        >>> expose.compose()
        {'env': {'CONTAINER_HOST': 'ssh://localhost:2222'}}

    Usage:
        The Expose feature is typically used in devcontainer configurations to
        enable container access to host services or network endpoints. Socket
        mode is commonly used for Docker-in-Docker scenarios, while address
        mode is used for SSH or other network service access.
    """

    socket: Optional[Socket] = Field(None, description="Socket paths")
    address: Optional[URL] = Field(None, description="Connection URL")

    @model_validator(mode="after")
    def check_exactly_one(self):
        """
        Exactly one of 'socket' or 'address' must be present (XOR).
        """
        if (self.socket is None) == (self.address is None):
            raise ValueError(
                "Exactly one of 'socket' or 'address' must be set in Expose."
            )
        return self

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the Expose feature into a dictionary according to the devcontainer spec.

        This method transforms the Expose feature configuration into the appropriate
        devcontainer specification format. The composition behavior depends on the
        configured mode:

        - **Socket Mode**: Creates a 'mounts' configuration that mounts the specified
          Unix socket into the container. The socket path is converted to a string
          representation and added to the mounts list.

        - **Address Mode**: Creates an environment variable configuration by setting
          the CONTAINER_HOST variable to the string representation of the URL. This
          is achieved by creating an Env feature instance and composing it.

        The method ensures that only the relevant configuration is included based
        on which mode is active, maintaining the XOR constraint at the composition
        level.

        Returns:
            Dict[str, Any]: A dictionary containing the devcontainer-compatible
                configuration. For socket mode, returns {'mounts': [socket_path]}.
                For address mode, returns {'env': {'CONTAINER_HOST': url_string}}.

        Examples:
            >>> # Socket mode composition
            >>> socket = Socket(path="/var/run/docker.sock")
            >>> expose = Expose(socket=socket)
            >>> expose.compose()
            {'mounts': ['/var/run/docker.sock']}

            >>> # Address mode composition
            >>> url = URL(scheme=URLScheme.TCP, host="localhost", port=8080)
            >>> expose = Expose(address=url)
            >>> expose.compose()
            {'env': {'CONTAINER_HOST': 'tcp://localhost:8080'}}

            >>> # Mixed configuration (will raise ValueError during validation)
            >>> expose = Expose(socket=socket, address=url)
            >>> expose.compose()  # This will fail validation
        """
        composed = {}
        if self.socket:
            composed["mounts"] = [str(self.socket)]
        if self.address:
            composed.update(
                Env(key="CONTAINER_HOST", value=str(self.address)).compose()
            )
        return composed


class Image(Feature):
    """
    Represents a container image configuration for devcontainer specification.

    This class defines the structure for specifying container images in the devcontainer
    configuration. It supports various image naming formats including repository-based
    images with optional tags, and standalone image names.

    Attributes:
        repository (Optional[ImageRepositoryIdentifier]): The container image repository
            identifier. This can be a Docker Hub username, organization name, or custom
            registry hostname. If None, the image is assumed to be from the default
            registry (typically Docker Hub).
        name (Identifier): The container image name. This is a required field that
            specifies the base name of the image (e.g., "ubuntu", "python", "node").
        tag (Optional[ImageTagIdentifier]): The container image tag that specifies
            the version or variant of the image. If None, the default "latest" tag
            is typically used by the container runtime.

    Validation Rules:
        - The name field is required and cannot be None
        - Repository and tag are optional but must be valid identifiers when provided
        - The combination of repository, name, and tag must form a valid container
          image reference according to Docker naming conventions

    Examples:
        >>> # Simple image name (uses default registry and latest tag)
        >>> image = Image(name="ubuntu")
        >>> str(image)
        'ubuntu'

        >>> # Repository with image name
        >>> image = Image(repository="library", name="python")
        >>> str(image)
        'library/python'

        >>> # Full image reference with repository, name, and tag
        >>> image = Image(repository="microsoft", name="vscode-devcontainers", tag="latest")
        >>> str(image)
        'microsoft/vscode-devcontainers:latest'

        >>> # Custom registry with image and tag
        >>> image = Image(repository="registry.example.com/project", name="app", tag="v1.0.0")
        >>> str(image)
        'registry.example.com/project/app:v1.0.0'
    """

    repository: Optional[ImageRepositoryIdentifier] = Field(
        None, description="Container image repository"
    )
    name: Identifier = Field(..., description="Container image name")
    tag: Optional[ImageTagIdentifier] = Field(None, description="Container image tag")

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the Image feature into a dictionary according to the devcontainer spec.

        This method transforms the Image configuration into the appropriate devcontainer
        specification format. The composition logic handles different image naming
        patterns based on the provided attributes:

        - **Simple Image Name**: When only the name is provided, returns the name as-is.
          This assumes the image is available in the default registry (typically Docker Hub)
          and uses the default "latest" tag.

        - **Repository + Name**: When both repository and name are provided but no tag,
          combines them with a forward slash separator. This format is commonly used
          for images from specific organizations or users on Docker Hub.

        - **Full Reference**: When repository, name, and tag are all provided, creates
          a complete image reference with the format "repository/name:tag". This is
          the most explicit format and is recommended for production environments.

        The method ensures that the resulting image reference follows Docker naming
        conventions and is compatible with the devcontainer specification.

        Returns:
            Dict[str, Any]: A dictionary containing the devcontainer-compatible
                image configuration. The structure is: {"image": "image_reference"}
                where image_reference follows Docker naming conventions.

        Examples:
            >>> # Simple image name
            >>> image = Image(name="ubuntu")
            >>> image.compose()
            {'image': 'ubuntu'}

            >>> # Repository with image name
            >>> image = Image(repository="library", name="python")
            >>> image.compose()
            {'image': 'library/python'}

            >>> # Full image reference
            >>> image = Image(repository="microsoft", name="vscode-devcontainers", tag="latest")
            >>> image.compose()
            {'image': 'microsoft/vscode-devcontainers:latest'}

            >>> # Custom registry with tag
            >>> image = Image(repository="registry.example.com/project", name="app", tag="v1.0.0")
            >>> image.compose()
            {'image': 'registry.example.com/project/app:v1.0.0'}
        """
        composed = {}
        if self.repository and not self.tag:
            composed["image"] = f"{self.repository}/{self.name}"
        elif self.repository and self.tag:
            composed["image"] = f"{self.repository}/{self.name}:{self.tag}"
        elif not self.repository and self.tag:
            composed["image"] = f"{self.name}:{self.tag}"
        else:
            composed["image"] = self.name
        return composed


class Build(Feature):
    """
    Build configuration for devcontainer.

    This class represents the build configuration for a development container.
    It allows you to specify how the container image should be built from a
    containerfile (Dockerfile or Containerfile) rather than using a pre-built image.
    This is useful when you need custom container images with specific dependencies,
    tools, or configurations for your development environment.

    The Build feature supports multi-stage builds through the target parameter,
    allowing you to build optimized images by specifying which build stage to use
    as the final image. The context parameter enables building from a specific
    directory, which is useful when your containerfile is not in the root of
    your project.

    Attributes:
        container_file (RelativePath): The path to the containerfile (Dockerfile
            or Containerfile) relative to the build context. This file contains
            the instructions for building the container image. Required field.
        context (Optional[RelativePath]): The path to the build context directory.
            This is the directory that contains the containerfile and any files
            that need to be copied into the image during the build process.
            If not specified, defaults to the workspace root.
        target (Optional[Identifier]): The target build stage to use from a
            multi-stage containerfile. This allows you to build only a specific
            stage of the containerfile, which is useful for creating optimized
            images. If not specified, builds the final stage.

    Examples:
        >>> # Basic build with containerfile
        >>> build = Build(container_file="Dockerfile")

        >>> # Build with custom context
        >>> build = Build(
        ...     container_file="docker/Dockerfile",
        ...     context="docker"
        ... )

        >>> # Multi-stage build with target
        >>> build = Build(
        ...     container_file="Dockerfile",
        ...     target="development"
        ... )

        >>> # Complete build configuration
        >>> build = Build(
        ...     container_file="docker/Dockerfile.dev",
        ...     context="docker",
        ...     target="production"
        ... )

    Validation:
        - Container file path must be a valid relative path
        - Context path must be a valid relative path if provided
        - Target must be a valid identifier if provided
        - All paths are relative to the workspace root
    """

    model_config = {"populate_by_name": True}

    container_file: RelativePath = Field(
        ..., alias="container-file", description="Path to the containerfile"
    )
    context: Optional[RelativePath] = Field(
        None, description="Path to the build context"
    )
    target: Optional[Identifier] = Field(None, description="Target build stage")

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the build configuration into a dictionary according to the devcontainer spec.

        This method converts the Build object into a dictionary format that follows the
        devcontainer specification for build configurations. The resulting dictionary
        contains a "build" key with sub-keys for the containerfile, context, and target
        parameters as needed.

        The method handles the following scenarios:
        - **Basic Build**: When only container_file is provided, creates a simple build
          configuration with just the dockerFile parameter.

        - **Build with Context**: When both container_file and context are provided,
          includes the context parameter to specify the build directory.

        - **Multi-stage Build**: When target is provided, includes the target parameter
          to specify which build stage to use from the containerfile.

        - **Complete Build**: When all parameters are provided, creates a comprehensive
          build configuration with all available options.

        The method ensures that only non-None values are included in the output,
        following the principle of minimal configuration.

        Returns:
            Dict[str, Any]: A dictionary containing the devcontainer-compatible
                build configuration. The structure is:
                {
                    "build": {
                        "dockerFile": "path/to/containerfile",
                        "context": "path/to/context",  # optional
                        "target": "stage_name"         # optional
                    }
                }

        Examples:
            >>> # Basic build
            >>> build = Build(container_file="Dockerfile")
            >>> build.compose()
            {'build': {'dockerFile': 'Dockerfile'}}

            >>> # Build with context
            >>> build = Build(container_file="docker/Dockerfile", context="docker")
            >>> build.compose()
            {'build': {'dockerFile': 'docker/Dockerfile', 'context': 'docker'}}

            >>> # Multi-stage build
            >>> build = Build(container_file="Dockerfile", target="development")
            >>> build.compose()
            {'build': {'dockerFile': 'Dockerfile', 'target': 'development'}}

            >>> # Complete build configuration
            >>> build = Build(
            ...     container_file="docker/Dockerfile.dev",
            ...     context="docker",
            ...     target="production"
            ... )
            >>> build.compose()
            {
                'build': {
                    'dockerFile': 'docker/Dockerfile.dev',
                    'context': 'docker',
                    'target': 'production'
                }
            }
        """
        composed = {"build": {}}
        if self.container_file:
            composed["build"]["dockerFile"] = str(self.container_file)
        if self.context:
            composed["build"]["context"] = str(self.context)
        if self.target:
            composed["build"]["target"] = self.target
        return composed


class Network(Feature):
    """
    Represents a Docker network configuration for devcontainer specification.

    This class defines the structure for specifying Docker networks in the devcontainer
    configuration. It allows you to connect the development container to a specific
    Docker network, enabling communication with other containers on that network.

    Docker networks provide isolation and communication between containers. By specifying
    a network name, the development container will be connected to that network when
    it starts, allowing it to communicate with other containers that are also connected
    to the same network.

    Attributes:
        name (Identifier): The name of the Docker network to connect to. This must
            be a valid identifier following the pattern: alphanumeric characters,
            hyphens, and underscores. The network must exist or be created before
            the container starts.

    Validation Rules:
        - The name field is required and cannot be None
        - The name must be a valid identifier following Docker naming conventions
        - The network must exist in the Docker environment when the container starts

    Examples:
        >>> # Connect to a specific network
        >>> network = Network(name="my-app-network")
        >>> network.compose()
        {'runArgs': ['--network=my-app-network']}

        >>> # Connect to a database network
        >>> network = Network(name="database-network")
        >>> network.compose()
        {'runArgs': ['--network=database-network']}

        >>> # Connect to a development network
        >>> network = Network(name="dev-network")
        >>> network.compose()
        {'runArgs': ['--network=dev-network']}
    """

    name: Identifier = Field(..., description="Network name")

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the Network feature into a dictionary according to the devcontainer spec.

        This method transforms the Network feature configuration into the appropriate
        devcontainer specification format. It creates a 'runArgs' configuration that
        specifies the Docker network to connect to when the container starts.

        The composition creates a Docker run argument in the format '--network=network_name'
        which instructs the container runtime to connect the development container
        to the specified Docker network. This enables network communication between
        the development container and other containers on the same network.

        Returns:
            Dict[str, Any]: A dictionary containing the devcontainer-compatible
                network configuration. The structure is: {"runArgs": ["--network=name"]}
                where name is the Docker network identifier.

        Examples:
            >>> # Basic network configuration
            >>> network = Network(name="app-network")
            >>> network.compose()
            {'runArgs': ['--network=app-network']}

            >>> # Database network configuration
            >>> network = Network(name="postgres-network")
            >>> network.compose()
            {'runArgs': ['--network=postgres-network']}

            >>> # Development environment network
            >>> network = Network(name="dev-env")
            >>> network.compose()
            {'runArgs': ['--network=dev-env']}
        """
        return {"runArgs": [f"--network={self.name}"]}


class Workspace(Feature):
    """
    Workspace configuration for devcontainer.

    This class represents the workspace configuration for a development container.
    It defines how the workspace is set up within the container, including the
    workspace name, folder location, and volume mounting configuration. The workspace
    is the primary directory where the development work takes place and is typically
    mounted as a Docker volume to persist data and enable collaboration.

    The Workspace feature creates a named workspace that can be referenced by other
    parts of the devcontainer configuration. It automatically sets up volume mounting
    to ensure that the workspace folder is properly mounted and accessible within
    the container. This is essential for maintaining data persistence and enabling
    real-time file synchronization between the host and container environments.

    Attributes:
        name (Identifier): The name of the workspace. This identifier is used to
            reference the workspace in other parts of the devcontainer configuration
            and must be unique within the container context.
        folder (AbsolutePath): The absolute path where the workspace will be located
            inside the container. This is the directory where the development work
            will take place and where source code, configuration files, and other
            project artifacts will be stored.
        volume_name (Identifier): The name of the Docker volume that will be used
            to mount the workspace. This volume ensures data persistence and enables
            the workspace to survive container restarts. The volume name must be
            a valid Docker volume identifier.

    Validation Rules:
        - All fields are required and cannot be None
        - The folder must be an absolute path
        - The name and volume_name must be valid identifiers
        - The volume_name must be unique across all workspaces in the same container

    Examples:
        >>> # Basic workspace configuration
        >>> workspace = Workspace(
        ...     name="my-project",
        ...     folder="/workspace",
        ...     volume_name="project-volume"
        ... )

        >>> # Workspace with custom folder path
        >>> workspace = Workspace(
        ...     name="backend-service",
        ...     folder="/app/src",
        ...     volume_name="backend-workspace"
        ... )

        >>> # Workspace for a specific development environment
        >>> workspace = Workspace(
        ...     name="frontend-dev",
        ...     folder="/home/developer/frontend",
        ...     volume_name="frontend-workspace"
        ... )
    """

    model_config = {"populate_by_name": True}

    name: Identifier = Field(..., description="Workspace name")
    folder: AbsolutePath = Field(
        ...,
        description="Workspace folder",
    )
    volume_name: Identifier = Field(
        ...,
        alias="volume-name",
        description="Workspace volume name",
    )

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the Workspace feature into a dictionary according to the devcontainer spec.

        This method transforms the Workspace feature configuration into the appropriate
        devcontainer specification format. It creates a complete workspace configuration
        that includes the workspace name, folder location, and automatic volume mounting.

        The composition creates three key components:

        - **name**: The workspace identifier that can be referenced by other features
        - **workspaceFolder**: The absolute path where the workspace is located in the container
        - **workspaceMount**: An automatically generated Mount configuration that creates
          a Docker volume mount for the workspace folder

        The workspaceMount is automatically created using the volume_name as the source
        and the folder as the target, with the mount type set to VOLUME. This ensures
        that the workspace data is persisted in a Docker volume and survives container
        restarts.

        Returns:
            Dict[str, Any]: A dictionary containing the devcontainer-compatible
                workspace configuration. The structure includes:
                - "name": The workspace identifier
                - "workspaceFolder": The workspace folder path as a string
                - "workspaceMount": A string representation of the volume mount configuration

        Examples:
            >>> # Basic workspace composition
            >>> workspace = Workspace(
            ...     name="my-project",
            ...     folder="/workspace",
            ...     volume_name="project-volume"
            ... )
            >>> workspace.compose()
            {
                'name': 'my-project',
                'workspaceFolder': '/workspace',
                'workspaceMount': 'Mount(source=project-volume, target=/workspace, type=volume)'
            }

            >>> # Workspace with custom folder path
            >>> workspace = Workspace(
            ...     name="backend",
            ...     folder="/app/src",
            ...     volume_name="backend-workspace"
            ... )
            >>> workspace.compose()
            {
                'name': 'backend',
                'workspaceFolder': '/app/src',
                'workspaceMount': 'Mount(source=backend-workspace, target=/app/src, type=volume)'
            }

            >>> # Workspace for development environment
            >>> workspace = Workspace(
            ...     name="frontend-dev",
            ...     folder="/home/developer/frontend",
            ...     volume_name="frontend-workspace"
            ... )
            >>> workspace.compose()
            {
                'name': 'frontend-dev',
                'workspaceFolder': '/home/developer/frontend',
                'workspaceMount': 'Mount(source=frontend-workspace, target=/home/developer/frontend, type=volume)'
            }
        """
        composed = {
            "name": self.name,
            "workspaceFolder": str(self.folder),
            "workspaceMount": str(
                Mount(
                    source=self.volume_name, target=self.folder, type=MountType.VOLUME
                )
            ),
        }
        return composed


class Extensions(Feature):
    """
    Extensions configuration for devcontainer.

    This class represents the extensions configuration for a development container.
    It allows you to specify VS Code extensions that should be automatically installed
    and enabled when the development container starts. This is useful for ensuring
    that all developers working on the project have the same set of extensions
    available, providing a consistent development experience across the team.

    The Extensions feature creates a 'customizations' configuration that instructs
    VS Code to install and enable the specified extensions when the development
    container is created. This ensures that all necessary development tools,
    language support, debugging capabilities, and other extensions are available
    without manual installation.

    Attributes:
        vscode (List[Extension]): A list of VS Code extensions to install and enable
            in the development container. Each extension is specified using its
            unique identifier (e.g., "ms-python.python" for the Python extension).
            The list must contain at least one extension and cannot exceed 100
            extensions to maintain reasonable performance and avoid conflicts.

    Validation Rules:
        - The vscode field is required and cannot be None
        - The list must contain at least one extension (min_length=1)
        - The list cannot exceed 100 extensions (max_length=100)
        - Each extension must be a valid VS Code extension identifier

    Examples:
        >>> # Basic extensions configuration
        >>> extensions = Extensions(vscode=[
        ...     "ms-python.python",
        ...     "ms-vscode.vscode-typescript-next"
        ... ])

        >>> # Extensions for Python development
        >>> extensions = Extensions(vscode=[
        ...     "ms-python.python",
        ...     "ms-python.black-formatter",
        ...     "ms-python.flake8",
        ...     "ms-python.pylint"
        ... ])

        >>> # Extensions for web development
        >>> extensions = Extensions(vscode=[
        ...     "ms-vscode.vscode-typescript-next",
        ...     "bradlc.vscode-tailwindcss",
        ...     "esbenp.prettier-vscode",
        ...     "ms-vscode.vscode-eslint"
        ... ])
    """

    vscode: List[Extension] = Field(
        ..., min_length=1, max_length=100, description="List of vscode extensions"
    )

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the Extensions feature into a dictionary according to the devcontainer spec.

        This method transforms the Extensions feature configuration into the appropriate
        devcontainer specification format. It creates a 'customizations' configuration
        that specifies VS Code extensions to be automatically installed and enabled
        when the development container starts.

        The composition creates a nested structure under 'customizations.vscode.extensions'
        that contains the list of extension identifiers. This format is compatible
        with the VS Code devcontainer specification and ensures that the specified
        extensions are installed during container creation.

        The method iterates through the vscode extensions list and includes each
        extension identifier in the final configuration. This allows for dynamic
        extension management based on the project's requirements.

        Returns:
            Dict[str, Any]: A dictionary containing the devcontainer-compatible
                extensions configuration. The structure is:
                {
                    "customizations": {
                        "vscode": {
                            "extensions": ["extension1", "extension2", ...]
                        }
                    }
                }
                where each extension is a valid VS Code extension identifier.

        Examples:
            >>> # Basic extensions composition
            >>> extensions = Extensions(vscode=["ms-python.python"])
            >>> extensions.compose()
            {
                'customizations': {
                    'vscode': {
                        'extensions': ['ms-python.python']
                    }
                }
            }

            >>> # Multiple extensions composition
            >>> extensions = Extensions(vscode=[
            ...     "ms-python.python",
            ...     "ms-vscode.vscode-typescript-next",
            ...     "esbenp.prettier-vscode"
            ... ])
            >>> extensions.compose()
            {
                'customizations': {
                    'vscode': {
                        'extensions': [
                            'ms-python.python',
                            'ms-vscode.vscode-typescript-next',
                            'esbenp.prettier-vscode'
                        ]
                    }
                }
            }

            >>> # Development tools extensions
            >>> extensions = Extensions(vscode=[
            ...     "ms-python.python",
            ...     "ms-python.black-formatter",
            ...     "ms-python.flake8",
            ...     "ms-python.pylint",
            ...     "ms-vscode.vscode-eslint"
            ... ])
            >>> extensions.compose()
            {
                'customizations': {
                    'vscode': {
                        'extensions': [
                            'ms-python.python',
                            'ms-python.black-formatter',
                            'ms-python.flake8',
                            'ms-python.pylint',
                            'ms-vscode.vscode-eslint'
                        ]
                    }
                }
            }
        """
        composed = {
            "customizations": {
                "vscode": {"extensions": [extension for extension in self.vscode]}
            }
        }
        return composed


class Container(Feature):
    """
    Container configuration for devcontainer specification.

    This class represents the main container configuration for a development container
    environment. It serves as the primary container feature that orchestrates all
    other container-related features including workspace setup, runtime configuration,
    networking, image or build configuration, port exposure, and VS Code extensions.

    The Container class is the central component that defines how a development
    container should be configured and behaves. It combines multiple features into
    a single, cohesive configuration that can be used by the devcontainer runtime
    to create and manage development environments.

    The container configuration supports two mutually exclusive approaches for
    defining the container image:
    - **Image-based**: Uses a pre-built Docker image from a registry
    - **Build-based**: Builds a custom image from a Dockerfile or Containerfile

    Attributes:
        workspace (Workspace): The workspace configuration that defines the
            development environment's workspace setup, including folder location
            and volume mounting. This is required and defines where the project
            code will be located within the container.
        runtime (Optional[Runtime]): Runtime configuration including user settings,
            environment variables, and mount points. If None, default runtime
            settings will be used.
        expose (Optional[Expose]): Port exposure configuration that defines which
            ports should be exposed from the container to the host. If None, no
            ports are exposed.
        image (Optional[Image]): Pre-built image configuration specifying the
            Docker image to use. Must be None if build is specified.
        build (Optional[Build]): Build configuration for creating a custom image
            from a Dockerfile or Containerfile. Must be None if image is specified.
        network (Optional[Network]): Network configuration for connecting the
            container to specific Docker networks. If None, the container uses
            the default network.
        extensions (Optional[Extensions]): VS Code extensions configuration that
            specifies which extensions should be installed in the development
            environment. If None, no custom extensions are installed.

    Validation Rules:
        - The workspace field is required and cannot be None
        - Exactly one of image or build must be specified (mutually exclusive)
        - All other fields are optional and can be None
        - When image is specified, build must be None
        - When build is specified, image must be None

    Examples:
        >>> # Basic container with image
        >>> container = Container(
        ...     workspace=Workspace(
        ...         name="my-project",
        ...         folder="/workspace",
        ...         volume_name="project-volume"
        ...     ),
        ...     image=Image(name="python:3.11-slim")
        ... )

        >>> # Container with build configuration
        >>> container = Container(
        ...     workspace=Workspace(
        ...         name="backend-service",
        ...         folder="/app",
        ...         volume_name="backend-workspace"
        ...     ),
        ...     build=Build(container_file="Dockerfile.dev"),
        ...     runtime=Runtime(user="developer"),
        ...     expose=Expose(ports=[8080, 5432])
        ... )

        >>> # Complete container configuration
        >>> container = Container(
        ...     workspace=Workspace(
        ...         name="full-stack-app",
        ...         folder="/workspace",
        ...         volume_name="app-workspace"
        ...     ),
        ...     image=Image(name="node:18-alpine"),
        ...     runtime=Runtime(
        ...         user=Users(remote="host-user", container="dev-user"),
        ...         env=[Env(key="NODE_ENV", value="development", type=EnvType.CONTAINER)]
        ...     ),
        ...     expose=Expose(ports=[3000, 3001]),
        ...     network=Network(name="app-network"),
        ...     extensions=Extensions(vscode=["ms-vscode.vscode-typescript-next"])
        ... )
    """

    workspace: Workspace
    runtime: Optional[Runtime] = None
    expose: Optional[Expose] = None
    image: Optional[Image] = None
    build: Optional[Build] = None
    network: Optional[Network] = None
    extensions: Optional[Extensions] = None

    @model_validator(mode="after")
    def check_image_or_build(self):
        """
        Validate that exactly one of 'image' or 'build' is specified.

        This validator ensures that the container configuration follows the devcontainer
        specification requirement that exactly one of image or build configuration
        must be provided. This is a mutual exclusion constraint where both cannot
        be specified simultaneously, and neither can be omitted.

        Raises:
            ValueError: If neither image nor build is specified, or if both are specified.

        Returns:
            Container: The validated container instance.
        """
        if not self.image and not self.build:
            raise ValueError(
                "At least one of 'image' or 'build' must be set in ContainerModel."
            )
        if self.image and self.build:
            raise ValueError(
                "Only one of 'image' or 'build' can be set in ContainerModel."
            )
        return self

    @override
    def compose(self) -> Dict[str, Any]:
        """
        Compose the container configuration into a dictionary according to the devcontainer spec.

        This method transforms the Container feature configuration into the appropriate
        devcontainer specification format. It combines all the individual feature
        configurations (workspace, runtime, expose, image/build, network, extensions)
        into a single, cohesive dictionary that can be used by the devcontainer runtime.

        The composition process includes each configured feature by calling its respective
        compose() method and merging the results into the final container configuration.
        Only features that are configured (not None) are included in the final output.

        The resulting dictionary structure follows the devcontainer specification format,
        where each feature contributes its specific configuration keys and values to
        the overall container configuration.

        Returns:
            Dict[str, Any]: A dictionary containing the complete devcontainer-compatible
                container configuration. The structure includes all configured features
                with their respective configuration keys and values as defined by the
                devcontainer specification.

        Examples:
            >>> # Basic container composition
            >>> container = Container(
            ...     workspace=Workspace(
            ...         name="simple-project",
            ...         folder="/workspace",
            ...         volume_name="project-volume"
            ...     ),
            ...     image=Image(name="python:3.11")
            ... )
            >>> container.compose()
            {
                'workspace': {'name': 'simple-project', 'folder': '/workspace', 'volumeName': 'project-volume'},
                'image': {'image': 'python:3.11'}
            }

            >>> # Container with multiple features
            >>> container = Container(
            ...     workspace=Workspace(
            ...         name="web-app",
            ...         folder="/app",
            ...         volume_name="web-workspace"
            ...     ),
            ...     build=Build(container_file="Dockerfile"),
            ...     runtime=Runtime(user="developer"),
            ...     expose=Expose(ports=[8080])
            ... )
            >>> container.compose()
            {
                'workspace': {'name': 'web-app', 'folder': '/app', 'volumeName': 'web-workspace'},
                'build': {'build': {'dockerFile': 'Dockerfile'}},
                'runtime': {'remoteUser': 'developer', 'containerUser': 'developer'},
                'expose': {'forwardPorts': [8080]}
            }

            >>> # Complete container with all features
            >>> container = Container(
            ...     workspace=Workspace(
            ...         name="full-stack",
            ...         folder="/workspace",
            ...         volume_name="full-workspace"
            ...     ),
            ...     image=Image(name="node:18"),
            ...     runtime=Runtime(
            ...         user=Users(remote="host", container="dev"),
            ...         env=[Env(key="DEBUG", value="true", type=EnvType.CONTAINER)]
            ...     ),
            ...     expose=Expose(ports=[3000, 3001]),
            ...     network=Network(name="app-network"),
            ...     extensions=Extensions(vscode=["ms-vscode.vscode-typescript-next"])
            ... )
            >>> container.compose()
            {
                'workspace': {'name': 'full-stack', 'folder': '/workspace', 'volumeName': 'full-workspace'},
                'image': {'image': 'node:18'},
                'runtime': {
                    'remoteUser': 'host',
                    'containerUser': 'dev',
                    'remoteEnv': {},
                    'containerEnv': {'DEBUG': 'true'}
                },
                'expose': {'forwardPorts': [3000, 3001]},
                'network': {'runArgs': ['--network=app-network']},
                'extensions': {
                    'customizations': {
                        'vscode': {
                            'extensions': ['ms-vscode.vscode-typescript-next']
                        }
                    }
                }
            }
        """
        composed = {}
        if self.workspace:
            composed[Workspace.feature_name()] = self.workspace.compose()
        if self.runtime:
            composed[Runtime.feature_name()] = self.runtime.compose()
        if self.expose:
            composed[Expose.feature_name()] = self.expose.compose()
        if self.image:
            composed[Image.feature_name()] = self.image.compose()
        if self.build:
            composed[Build.feature_name()] = self.build.compose()
        if self.network:
            composed[Network.feature_name()] = self.network.compose()
        if self.extensions:
            composed[Extensions.feature_name()] = self.extensions.compose()
        return composed
