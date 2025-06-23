from enum import Enum
from typing import Dict, Union
from pydantic import BaseModel, Field, RootModel, model_validator

ReservedPolicyKeys = {
    "container": "container",
    "folder": "folder",
    "file": "file"
}

class Policy(BaseModel):
    """
    Base class for all policy types in the system.

    This abstract base class provides the foundation for all policy implementations.
    Policies define rules and behaviors for different aspects of the system, such as
    container management, folder operations, and file handling.

    Attributes:
        None - This is a base class with no specific attributes

    Examples:
        # Direct instantiation is not intended - use specific policy types
        # ContainerPolicy, FolderPolicy, or FilePolicy instead

    Note:
        This class should not be instantiated directly. Use one of the specific
        policy implementations that inherit from this base class.
    """

class FolderCreatePolicy(str, Enum):
    ALWAYS = "always"
    NEVER = "never"
    ASK = "ask"

class FolderPolicy(Policy):
    """
    Represents a folder policy that defines rules for folder creation operations.

    This policy class inherits from the base Policy class and provides configuration
    options for controlling how folders are created during project operations.
    The policy allows fine-grained control over folder creation behavior through
    the FolderCreatePolicy enum.

    Attributes:
        create (FolderCreatePolicy): The folder creation policy that determines
            how folders should be created. Defaults to FolderCreatePolicy.ASK,
            which prompts the user for confirmation before creating folders.

    Examples:
        >>> # Create a policy that always creates folders without prompting
        >>> policy = FolderPolicy(create=FolderCreatePolicy.ALWAYS)

        >>> # Create a policy that never creates folders automatically
        >>> policy = FolderPolicy(create=FolderCreatePolicy.NEVER)

        >>> # Create a policy that asks for confirmation (default behavior)
        >>> policy = FolderPolicy(create=FolderCreatePolicy.ASK)

    Note:
        This policy is used in conjunction with the main Policies class to
        configure folder-related operations across the system. The create
        attribute controls whether folders are created automatically, never
        created, or whether user confirmation is required.
    """

    create: FolderCreatePolicy = Field(FolderCreatePolicy.ASK, description="The folder create policy")


class FileWritePolicy(str, Enum):
    NEVER = "never"
    OVERWRITE = "overwrite"
    SKIP = "skip"
    ASK = "ask"

class FilePolicy(Policy):
    """
    Represents a file policy that defines rules for file write operations.

    This policy class inherits from the base Policy class and provides configuration
    options for controlling how files are written during project operations.
    The policy allows fine-grained control over file write behavior through
    the FileWritePolicy enum.

    Attributes:
        write (FileWritePolicy): The file write policy that determines how files
            should be written when conflicts occur. Defaults to FileWritePolicy.ASK,
            which prompts the user for confirmation before writing files.

    Examples:
        >>> # Create a policy that always overwrites existing files
        >>> policy = FilePolicy(write=FileWritePolicy.OVERWRITE)

        >>> # Create a policy that never overwrites existing files
        >>> policy = FilePolicy(write=FileWritePolicy.NEVER)

        >>> # Create a policy that skips files that already exist
        >>> policy = FilePolicy(write=FileWritePolicy.SKIP)

        >>> # Create a policy that asks for confirmation (default behavior)
        >>> policy = FilePolicy(write=FileWritePolicy.ASK)

    Note:
        This policy is used in conjunction with the main Policies class to
        configure file-related operations across the system. The write
        attribute controls whether files are overwritten automatically, never
        overwritten, skipped if they exist, or whether user confirmation is required.
    """

    write: FileWritePolicy = Field(FileWritePolicy.ASK, description="The file write policy")


class ContainerBackendPolicy(str, Enum):
    DOCKER = "docker"
    PODMAN = "podman"
    ANY = "any"

class ContainerPolicy(Policy):
    """
    Represents a container policy that defines rules for container backend operations.

    This policy class inherits from the base Policy class and provides configuration
    options for controlling which container backend is used for project operations.
    The policy allows specification of the preferred container runtime through
    the ContainerBackendPolicy enum.

    Attributes:
        backend (ContainerBackendPolicy): The container backend policy that determines
            which container runtime should be used. Defaults to ContainerBackendPolicy.ANY,
            which allows the system to choose the most appropriate backend available.

    Examples:
        >>> # Create a policy that specifically uses Docker
        >>> policy = ContainerPolicy(backend=ContainerBackendPolicy.DOCKER)

        >>> # Create a policy that specifically uses Podman
        >>> policy = ContainerPolicy(backend=ContainerBackendPolicy.PODMAN)

        >>> # Create a policy that allows any backend (default behavior)
        >>> policy = ContainerPolicy(backend=ContainerBackendPolicy.ANY)

    Note:
        This policy is used in conjunction with the main Policies class to
        configure container-related operations across the system. The backend
        attribute controls which container runtime (Docker, Podman, or any available)
        should be used for container operations. When set to ANY, the system
        will automatically select the most suitable backend based on availability
        and system configuration.
    """

    backend: ContainerBackendPolicy = Field(ContainerBackendPolicy.ANY, description="The container backend policy")


class Policies(RootModel[Dict[str, Union[ContainerPolicy, FolderPolicy, FilePolicy]]]):
    """
    Represents a collection of policies that define rules and configurations for various system operations.

    This model inherits from Pydantic's RootModel and manages a dictionary of policy objects,
    where each key represents a specific policy type and the value contains the corresponding
    policy configuration. The model enforces validation rules to ensure that only valid
    policy types are included and that at least one policy is specified.

    The model supports three types of policies:
    - ContainerPolicy: Defines container backend preferences (Docker, Podman, or any)
    - FolderPolicy: Controls folder creation behavior (always, never, or ask)
    - FilePolicy: Manages file write operations (overwrite, skip, or ask)

    Attributes:
        root (Dict[str, Union[ContainerPolicy, FolderPolicy, FilePolicy]]): A dictionary
            containing policy configurations, where keys are policy types and values are
            the corresponding policy objects.

    Validation Rules:
        - At least one policy must be specified (non-empty dictionary)
        - Only reserved policy keys are allowed (container, folder, file)
        - Each policy object must be a valid instance of its respective policy type

    Examples:
        >>> # Create policies with container and folder configurations
        >>> policies = Policies({
        ...     "container": ContainerPolicy(backend=ContainerBackendPolicy.DOCKER),
        ...     "folder": FolderPolicy(create=FolderCreatePolicy.ALWAYS)
        ... })

        >>> # Create policies with all policy types
        >>> policies = Policies({
        ...     "container": ContainerPolicy(backend=ContainerBackendPolicy.PODMAN),
        ...     "folder": FolderPolicy(create=FolderCreatePolicy.NEVER),
        ...     "file": FilePolicy(write=FileWritePolicy.SKIP)
        ... })

    Raises:
        ValueError: If no policies are specified or if invalid policy keys are used.

    Note:
        This model is used throughout the system to configure behavior for container
        operations, folder management, and file handling. The validation ensures that
        only supported policy types are used and that the configuration is complete.
    """

    @model_validator(mode="after")
    def check_policies(self):
        """
        Validates the policies configuration to ensure it meets all requirements.

        This validator runs after the model is instantiated and performs the following checks:
        1. Ensures that at least one policy is specified (non-empty dictionary)
        2. Validates that all policy keys are from the reserved policy keys list
        3. Returns the validated model instance

        Validation Rules:
        - The policies dictionary must not be empty
        - All keys must be valid reserved policy keys (container, folder, file)
        - Invalid keys will result in a ValueError with a descriptive message

        Returns:
            Policies: The validated policies instance if all checks pass.

        Raises:
            ValueError: If the policies dictionary is empty or contains invalid keys.
                - "At least one policy must be specified" when no policies are provided
                - "Invalid policy key: {key}" when an unrecognized policy key is used

        Examples:
            >>> # Valid configuration
            >>> policies = Policies({"container": ContainerPolicy()})
            >>> validated = policies.check_policies()  # Passes validation

            >>> # Invalid configuration - empty dict
            >>> with pytest.raises(ValueError, match="At least one policy must be specified"):
            ...     Policies({})

            >>> # Invalid configuration - invalid key
            >>> with pytest.raises(ValueError, match="Invalid policy key: invalid"):
            ...     Policies({"invalid": ContainerPolicy()})

        Note:
            This validator is automatically called by Pydantic during model instantiation
            and ensures that the policies configuration is valid before the model can be used.
        """
        if len(self.root.keys()) == 0:
            raise ValueError("At least one policy must be specified")
        for key in self.root.keys():
            if key not in ReservedPolicyKeys.values():
                raise ValueError(f"Invalid policy key: {key}")
        return self