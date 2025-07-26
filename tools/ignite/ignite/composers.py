import json
import logging
import os
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional

import typer

from ignite.logging import FilesystemMessage
from ignite.models.container import (
    Build,
    Container,
    Expose,
    Extensions,
    Image,
    Network,
    Runtime,
)
from ignite.models.container import Workspace as ContainerWorkspace
from ignite.models.fs import FileTemplateVariables, ResolvedFile
from ignite.models.policies import (
    FileWritePolicy,
    FolderCreatePolicy,
    Policies,
    ReservedPolicyKeys,
)
from ignite.models.workspace import Workspace as WorkspaceModel
from ignite.resolvers import PathResolver

JSON_INDENT = 2


class Composer:
    """
    Base composer class for generating configuration files.

    This abstract base class provides common functionality for composers that generate
    various types of configuration files. It handles file system operations, user
    interactions, and logging for the composition process.

    The composer supports configurable policies for folder creation and file writing,
    allowing for flexible behavior when dealing with existing files and directories.
    It provides interactive prompts for user decisions when policies are set to ASK.

    Attributes:
        logger: Logger instance for the composer class
    """

    def __init__(self):
        """
        Initialize the Composer with a logger instance.

        Sets up logging for the composer class with propagation enabled to ensure
        log messages are properly handled by the parent logger hierarchy.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.propagate = True

    def compose(self) -> None:
        """
        Compose the configuration into a dictionary.

        This method should be implemented by subclasses to perform the actual
        composition logic. The base implementation is a placeholder that does nothing.

        Subclasses should override this method to:
        - Process their specific configuration models
        - Generate the appropriate data structures
        - Store the result for later use by the save method
        """
        pass

    def save(self, output_path: Path, policies: Policies) -> None:
        """
        Save the composed configuration to a file.

        This method should be implemented by subclasses to handle the specific
        file format and saving logic for their configuration type. The method
        uses the provided policies to determine how to handle folder creation
        and file writing operations.

        Args:
            output_path: Path where the configuration file should be saved.
            policies: The policies object containing folder and file policies
                     that determine how to handle directory creation and file writing.

        Raises:
            NotImplementedError: Always raised by the base class, subclasses must
            implement.
        """
        raise NotImplementedError("Subclass must implement this method.")

    def _ask_create_folder(self, output_path: Path) -> bool:
        """
        Ask the user if they want to create a folder.

        Prompts the user with a confirmation dialog to create a directory that
        doesn't exist. This is used when the folder creation policy is set to ASK.

        Args:
            output_path: Path to the folder that needs to be created

        Returns:
            bool: True if the user confirms folder creation, False otherwise
        """
        return typer.confirm(
            f"Folder '{output_path}' does not exist. Do you want to create it?"
        )

    def _ask_overwrite_file(self, output_path: Path) -> bool:
        """
        Ask the user if they want to overwrite an existing file.

        Prompts the user with a confirmation dialog to overwrite a file that
        already exists. This is used when the file write policy is set to ASK.

        Args:
            output_path: Path to the file that would be overwritten

        Returns:
            bool: True if the user confirms file overwrite, False otherwise
        """
        return typer.confirm(
            f"File '{output_path}' already exists. Do you want to overwrite it?"
        )

    def _save_file(
        self,
        output_path: Path,
        content: str,
        folder_policy: FolderCreatePolicy = FolderCreatePolicy.ASK,
        file_policy: FileWritePolicy = FileWritePolicy.ASK,
    ) -> None:
        """
        Save content to a file with configurable policies for folder creation and file
        writing.

        This method handles the complete file saving process including:
        - Validating that the output path is not a directory
        - Creating parent directories based on the folder creation policy
        - Handling existing files based on the file write policy
        - Writing the content to the file
        - Logging all filesystem operations

        The method supports four folder creation policies:
        - ASK: Prompt the user for permission to create folders
        - ALWAYS: Automatically create folders without prompting
        - NEVER: Raise an error if folders don't exist

        The method supports four file write policies:
        - ASK: Prompt the user for permission to overwrite existing files
        - SKIP: Skip writing if the file already exists
        - OVERWRITE: Automatically overwrite existing files
        - NEVER: Raise an error if the file already exists

        Args:
            output_path: Path where the file should be saved
            content: String content to write to the file
            folder_policy: Policy for handling parent directory creation
            file_policy: Policy for handling existing files

        Raises:
            ValueError: If output_path is a directory
            ValueError: If folder creation is needed but policy is NEVER
            ValueError: If file overwrite is needed but policy is NEVER
            ValueError: If unsupported folder or file policies are provided
        """
        if output_path.is_dir():
            raise ValueError(f"Path '{output_path}' is a directory.")

        base_path = output_path.parent
        if not base_path.exists():
            if folder_policy == FolderCreatePolicy.ASK:
                if self._ask_create_folder(base_path):
                    base_path.mkdir(parents=True, exist_ok=True)
                    FilesystemMessage.create_folder(base_path).log(self.logger)
                else:
                    FilesystemMessage.skip_folder(base_path).log(self.logger)
                    return
            elif folder_policy == FolderCreatePolicy.ALWAYS:
                base_path.mkdir(parents=True, exist_ok=True)
                FilesystemMessage.create_folder(base_path).log(self.logger)
            elif folder_policy == FolderCreatePolicy.NEVER:
                raise ValueError(
                    f"Folder '{base_path}' does not exist and policy is set to never."
                )
            else:
                raise ValueError(f"Unsupported folder create policy: {folder_policy}.")

        if output_path.exists():
            if file_policy == FileWritePolicy.ASK:
                if self._ask_overwrite_file(output_path):
                    FilesystemMessage.overwrite_file(output_path).log(self.logger)
                else:
                    FilesystemMessage.skip_file(output_path).log(self.logger)
                    return
            elif file_policy == FileWritePolicy.SKIP:
                FilesystemMessage.skip_file(output_path).log(self.logger)
                return
            elif file_policy == FileWritePolicy.NEVER:
                raise ValueError(
                    f"File '{output_path}' already exists and policy is set to never."
                )
            elif file_policy == FileWritePolicy.OVERWRITE:
                FilesystemMessage.overwrite_file(output_path).log(self.logger)
            else:
                raise ValueError(f"Unsupported file write policy: {file_policy}.")

        with open(output_path, "w") as f:
            f.write(content)
        FilesystemMessage.save_file(output_path).log(self.logger)
        return


class ContainerComposer(Composer):
    """
    A composer for creating devcontainer configurations.

    This class handles the composition of container configurations into devcontainer
    specification files. It processes container models and generates the necessary
    configuration files for development containers according to the devcontainer spec.

    The composer works with a container model that contains various features like
    workspace settings, runtime configurations, port exposures, build instructions,
    image specifications, network settings, and extensions. It ensures that features
    are composed in a specific order to maintain proper configuration structure.

    The composition process involves:
    1. Processing all container features in a predefined order
    2. Merging feature configurations according to their types (dict, list, or scalar)
    3. Generating a final configuration dictionary that follows the devcontainer spec
    4. Saving the configuration to a devcontainer.json file
    """

    def __init__(self, container: Container):
        """
        Initialize the ContainerComposer.

        Args:
            container: The container model containing features and configurations
                      to be composed into a devcontainer specification.
        """
        super().__init__()
        self.__container: Container = container
        self.__config: Optional[Dict] = None
        self.__feature_order = [
            ContainerWorkspace.feature_name(),
            Runtime.feature_name(),
            Expose.feature_name(),
            Build.feature_name(),
            Image.feature_name(),
            Network.feature_name(),
            Extensions.feature_name(),
        ]

    def compose(self) -> None:
        """
        Compose the container into a dictionary according to the devcontainer spec.

        This method processes all container features in a predefined order and
        merges their configurations into a single dictionary. The feature order
        ensures that dependencies and configurations are properly structured.

        The composition process:
        1. Creates an ordered dictionary to maintain feature order
        2. Gets all composed features from the container model
        3. Processes features in the predefined order
        4. Merges each feature's configuration using _add_feature
        5. Stores the final configuration for later saving

        Raises:
            ValueError: If the container model is invalid or cannot be processed.
        """
        features = OrderedDict()
        composed_features = self.__container.compose()
        for feature_key in self.__feature_order:
            if feature_key not in composed_features:
                continue
            feature = composed_features[feature_key]
            self._add_feature(features, feature)
        self.__config = features

    def _add_feature(self, features: Dict, feature: Dict) -> None:
        """
        Add a feature to the configuration with proper merging logic.

        This method handles the merging of feature configurations into the main
        configuration dictionary. It implements intelligent merging based on the
        type of configuration values:

        - For dictionaries: Updates existing dict with new key-value pairs
        - For lists: Extends existing list with new items
        - For other types: Replaces existing value with new value

        Args:
            features: The main configuration dictionary to merge into.
            feature: The feature configuration dictionary to merge.

        Note:
            This method modifies the features dictionary in-place by merging
            the feature configuration according to the merging rules.
        """
        for key, value in feature.items():
            if key in features and isinstance(features[key], dict):
                features[key].update(value)
            elif key in features and isinstance(features[key], list):
                features[key].extend(value)
            else:
                features[key] = value

    def save(self, output_path: Path, policies: Policies) -> None:
        """
        Save the composed configuration to a devcontainer.json file.

        This method saves the composed container configuration to a devcontainer.json
        file in the specified output path. The file is created in a .devcontainer
        subdirectory to follow the standard devcontainer specification structure.

        The method uses the provided policies to determine how to handle folder creation
        and file writing operations. It respects the folder creation policy for creating
        the .devcontainer directory and the file write policy for handling existing
        devcontainer.json files.

        Args:
            output_path: The base path where the devcontainer configuration
                        should be saved. The actual file will be created at
                        {output_path}/.devcontainer/devcontainer.json.
            policies: The policies object containing folder and file policies
                     that determine how to handle directory creation and file writing.

        Raises:
            ValueError: If the configuration has not been composed yet (compose()
                      method has not been called).
            ValueError: If the output path is invalid or cannot be created.
            ValueError: If folder creation is needed but policy is NEVER.
            ValueError: If file overwrite is needed but policy is NEVER.

        Note:
            The method uses the folder creation policy from
            policies.root[ReservedPolicyKeys.FOLDER].create
            and the file write policy from
            policies.root[ReservedPolicyKeys.FILE].write to determine
            the behavior for directory creation and file writing respectively.
        """
        if self.__config is None:
            raise ValueError("Configuration is not composed yet.")
        output_path = Path(output_path, ".devcontainer", "devcontainer.json")
        self._save_file(
            output_path=output_path,
            content=json.dumps(self.__config, indent=JSON_INDENT),
            folder_policy=policies.root[ReservedPolicyKeys.FOLDER].create,
            file_policy=policies.root[ReservedPolicyKeys.FILE].write,
        )


class WorkspaceComposer(Composer):
    """
    A composer for creating VS Code workspace configurations.

    This class handles the composition of workspace configurations into VS Code
    workspace files and project-specific files. It processes the workspace model,
    resolves project folders, and generates the necessary file specifications
    for a complete VS Code workspace setup.

    The composer works with a workspace model that contains projects and policies,
    and uses a path resolver to handle path transformations and folder resolution.
    It generates both the main workspace file (.code-workspace) and any project-specific
    files defined in the workspace configuration.
    """

    def __init__(self, workspace: WorkspaceModel, path_resolver: PathResolver):
        """
        Initialize the WorkspaceComposer.

        Args:
            workspace: The workspace model containing projects and policies.
            path_resolver: The path resolver for handling path transformations.
        """
        super().__init__()
        self.__workspace: WorkspaceModel = workspace
        self.__path_resolver: PathResolver = path_resolver
        self.__resolved_files: List[ResolvedFile] = None

    def compose(self) -> None:
        """
        Compose the workspace into a list of resolved files.

        This method processes the workspace configuration and creates the necessary
        file specifications. It generates both the main workspace file and any
        project-specific files defined in the workspace model.

        The composition process involves:
        1. Creating the main workspace file specification (.code-workspace)
        2. Resolving all project files and their configurations
        3. Combining all resolved files into a single list for later saving

        Raises:
            ValueError: If the workspace model is invalid or cannot be processed.
        """
        file_specification = self._resolve_file_specification()
        project_files = self._resolve_project_files()
        self.__resolved_files = [file_specification, *project_files]

    def _resolve_project_files(self) -> List[ResolvedFile]:
        """
        Resolve all project files in the workspace.

        This method processes all projects defined in the workspace model and
        creates resolved file objects for each project's configuration files.
        It uses the path resolver to handle path transformations and creates
        file content variables for template processing.

        Returns:
            A list of resolved file objects representing all project-specific
            configuration files in the workspace.

        Note:
            This method handles both user-defined projects and special reference
            projects, applying the appropriate path resolution and template
            variable substitution for each project.
        """
        resolved_project_files: List[ResolvedFile] = []
        original_cwd = Path.cwd()
        try:
            os.chdir(self.__path_resolver.user_context)
            resolved_project_variables = self.__workspace.resolve_project_variables()
        finally:
            os.chdir(original_cwd)
        resolved_project_folders = self.__workspace.resolve_project_folders(
            self.__path_resolver
        )
        for project_name, resolved_folders in resolved_project_folders.items():
            variables = resolved_project_variables.get(project_name, None)
            file_content_variables = FileTemplateVariables(
                project_name=project_name, variables=variables
            )
            for resolved_folder in resolved_folders:
                resolved_project_files.append(
                    resolved_folder.resolve(file_content_variables)
                )
            file_content_variables.check_variables_usage()
        return resolved_project_files

    def _resolve_file_specification(self) -> ResolvedFile:
        """
        Create the main VS Code workspace file specification.

        This method generates the primary workspace file (.code-workspace) that
        defines the folder structure and workspace-level settings for VS Code.
        The file contains the folder specifications for all projects in the
        workspace and any workspace-level settings.

        Returns:
            A resolved file object containing the workspace file specification
            with the path "workspace.code-workspace" and JSON content representing
            the workspace configuration.

        Note:
            The generated JSON content includes folder specifications and settings
            from the workspace model, formatted with proper indentation for
            readability.
        """
        return ResolvedFile(
            path="workspace.code-workspace",
            content=json.dumps(
                self.__workspace.resolve_file_specification().model_dump(
                    exclude_none=True
                ),
                indent=JSON_INDENT,
            ),
        )

    def save(self, output_path: Path, policies: Policies) -> None:
        """
        Save all resolved files to the specified output path.

        This method writes all the resolved files (workspace file and project files)
        to the filesystem at the specified output path. It handles path resolution,
        directory creation, and file writing according to the provided policies.

        The save process:
        1. Validates that files have been resolved (compose() has been called)
        2. Processes each resolved file, handling absolute path conversion
        3. Creates necessary directories and writes files using the provided policies
        4. Applies folder creation and file write policies from the policies
           configuration

        Args:
            output_path: The base path where all workspace files should be saved.
                         This path will be used as the root for all file operations.
            policies: The policies configuration that defines how to handle folder
                     creation and file writing operations.

        Raises:
            ValueError: If files have not been resolved yet (compose() not called).
            OSError: If file system operations fail (permissions, disk space, etc.).

        Note:
            The method uses the provided policies to determine how to handle directory
            creation and file overwriting. Absolute paths in resolved files are
            converted to relative paths within the output directory structure.
        """
        if self.__resolved_files is None:
            raise ValueError("Files are not resolved yet.")
        for resolved_file in self.__resolved_files:
            path = Path(resolved_file.path)
            if path.parts[0] == os.path.sep:
                path = Path(*path.parts[1:])
            self._save_file(
                output_path=Path(output_path, path),
                content=resolved_file.content,
                folder_policy=policies.root[ReservedPolicyKeys.FOLDER].create,
                file_policy=policies.root[ReservedPolicyKeys.FILE].write,
            )
