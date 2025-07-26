import pathlib
from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, RootModel, model_validator

from ignite.models.common import Identifier
from ignite.models.fs import RelativePath, ResolvedFolder
from ignite.models.settings import VSCodeFolder
from ignite.models.variables import ResolvedVariables, Variables


class ReservedProjectKey(str, Enum):
    REF = "ref"
    ROOT = "root"


user_project_key = Identifier
root_project_key = Literal[ReservedProjectKey.ROOT]
ref_project_key = Literal[ReservedProjectKey.REF]
project_key = Union[root_project_key, ref_project_key, user_project_key]


def _resolve_vscode_folder(vscode_folder: VSCodeFolder) -> List[ResolvedFolder]:
    resolved_folders: List[ResolvedFolder] = vscode_folder.resolve()
    for resolved_folder in resolved_folders:
        resolved_folder.destination = str(
            pathlib.Path(*[".vscode", *pathlib.Path(resolved_folder.destination).parts])
        )
        resolved_folder.sources = [
            str(pathlib.Path(*["vscode", *pathlib.Path(source).parts]))
            for source in resolved_folder.sources
        ]
    return resolved_folders


class RepositoryProject(BaseModel):
    """
    Represents a repository project with optional VSCode configuration.

    A RepositoryProject defines a project that is part of the repository structure
    and can optionally include VSCode workspace settings and tasks configuration.
    Unlike UserProject, RepositoryProject does not have a filesystem path as it
    is managed within the repository context.

    Attributes:
        variables: Optional variables configuration for the project.
            If provided, contains project-specific variables that can be used throughout
            the project configuration.
        vscode: Optional VSCode folder configuration containing settings and tasks for
            the project. If provided, will be resolved to generate .vscode/settings.json
            and .vscode/tasks.json files. If not provided, no VSCode configuration will
            be generated.

    Methods:
        resolve_folders: Resolves the VSCode configuration to a list of ResolvedFolder
                         objects that represent the files to be created in the project
                         directory.

    Example:
        ```python
        >>> # Minimal repository project without VSCode configuration
        >>> project = RepositoryProject()

        >>> # Repository project with variables and VSCode settings
        >>> variables = Variables({"ENV": "development", "DEBUG": "true"})
        >>> vscode_config = VSCodeFolder(
        ...     settings=[Folder({"python": [File("base")]})]
        ... )
        >>> project = RepositoryProject(variables=variables, vscode=vscode_config)

        >>> # Repository project with both settings and tasks
        >>> vscode_config = VSCodeFolder(
        ...     settings=[Folder({"python": [File("base")]})],
        ...     tasks=[Folder({"poetry": [File("build")]})]
        ... )
        >>> project = RepositoryProject(vscode=vscode_config)
        ```

    Validation:
        - variables: If provided, must be a valid Variables configuration
        - vscode: If provided, must be a valid VSCodeFolder configuration
    """

    variables: Optional[Variables] = Field(
        None, description="Optional variables configuration for the project"
    )

    vscode: Optional[VSCodeFolder] = Field(
        None, description="Optional VSCode folder configuration for the project"
    )

    def resolve_folders(self) -> List[ResolvedFolder]:
        """
        Resolve the VSCode configuration to a list of ResolvedFolder objects.

        This method processes the VSCode configuration and converts it into
        ResolvedFolder objects that represent the final VSCode configuration files to
        be generated. Each ResolvedFolder contains the source paths and destination
        file information needed for file merging operations.

        Returns:
            List[ResolvedFolder]: A list of ResolvedFolder objects representing
                the VSCode configuration files to be generated. The list will contain:
                - One ResolvedFolder for settings.json if settings are configured
                - One ResolvedFolder for tasks.json if tasks are configured
                - Empty list if no VSCode configuration is provided

        Examples:
            Basic resolution with settings:
            >>> vscode = VSCodeFolder(settings=[Folder({"python": [File("base")]})])
            >>> project = RepositoryProject(vscode=vscode)
            >>> resolved = project.resolve_folders()
            >>> # Returns: [ResolvedFolder(
            ...     sources=["vscode/settings/python/base"],
            ...     destination=".vscode/settings.json"
            ... )]

            Resolution with both configurations:
            >>> vscode = VSCodeFolder(
            ...     settings=[Folder({"python": [File("base")]})],
            ...     tasks=[Folder({"poetry": [File("build")]})]
            ... )
            >>> project = RepositoryProject(vscode=vscode)
            >>> resolved = project.resolve_folders()
            >>> # Returns: [
            ... #     ResolvedFolder(
            ...     sources=["vscode/settings/python/base"],
            ...     destination=".vscode/settings.json"
            ... ),
            ... #     ResolvedFolder(
            ...     sources=["vscode/tasks/poetry/build"],
            ...     destination=".vscode/tasks.json"
            ... )
            ... # ]

            No VSCode configuration:
            >>> project = RepositoryProject()
            >>> resolved = project.resolve_folders()
            >>> # Returns: []
        """
        resolved_folders: List[ResolvedFolder] = []
        if self.vscode:
            resolved_folders.extend(_resolve_vscode_folder(self.vscode))
        return resolved_folders


class UserProject(BaseModel):
    """
    Represents a user project with filesystem path, optional variables, and optional
    VSCode configuration.

    A UserProject defines a user-specific project that can be located anywhere on the
    filesystem, and can optionally include VSCode workspace settings, tasks
    configuration, and project-specific variables.

    Attributes:
        alias: An optional identifier that can be used as an alternative name for the
            project. If provided, must be a valid identifier string. If None, the
            project key will be used.
        path: The relative filesystem path where the project is located. Must be a valid
            relative path that exists or can be created.
        variables: Optional variables configuration for the project. If provided, must
            be a valid Variables object containing key-value pairs for project-specific
            configuration.
        vscode: Optional VSCode folder configuration containing settings and tasks for
            the project. If provided, will be resolved to generate .vscode/settings.json
            and .vscode/tasks.json files.

    Methods:
        resolve_folders: Resolves the VSCode configuration to a list of ResolvedFolder
            objects that represent the files to be created in the project directory.

    Example:
        ```python
        >>> # Minimal project with just a path
        >>> project = UserProject(path="/workspace/my-project")

        >>> # Project with alias, variables, and VSCode configuration
        >>> from ignite.models.common import Variables
        >>> vscode_config = VSCodeFolder(
        ...     settings=[Folder({"python": [File("base")]})],
        ...     tasks=[Folder({"poetry": [File("build")]})]
        ... )
        >>> project = UserProject(
        ...     path="my-project/",
        ...     alias="my-python-project",
        ...     variables=Variables({"pytest-root-directory": "tests"}),
        ...     vscode=vscode_config
        ... )
        ```

    Validation:
        - path: Must be a valid relative path
        - alias: If provided, must be a valid identifier string
        - variables: If provided, must be a valid Variables object
        - vscode: If provided, must be a valid VSCodeFolder configuration
    """

    alias: Optional[Identifier] = Field(
        None, description="The alias of the user project"
    )
    path: RelativePath = Field(..., description="The path of the user project")
    variables: Optional[Variables] = Field(
        None, description="Optional variables configuration for the project"
    )
    vscode: Optional[VSCodeFolder] = Field(
        None, description="Optional VSCode folder configuration for the project"
    )

    def resolve_folders(self) -> List[ResolvedFolder]:
        """
        Resolve the VSCode configuration to a list of ResolvedFolder objects.

        This method processes the optional VSCode configuration and returns a list of
        ResolvedFolder objects that represent the files to be created in the project
        directory. If no VSCode configuration is provided, returns an empty list.

        Returns:
            List[ResolvedFolder]: A list of resolved folders representing the VSCode
                configuration files to be created. Each ResolvedFolder
                contains the destination path and source files.

        Example:
            ```python
            >>> project = UserProject(
            ...     path="/workspace/my-project",
            ...     vscode=VSCodeFolder(settings=[Folder({"python": [File("base")]})])
            ... )
            >>> folders = project.resolve_folders()
            # Returns: [ResolvedFolder(destination=".vscode/settings.json",
            #           sources=["vscode/settings/python/base"])]
            ```
        """
        resolved_folders: List[ResolvedFolder] = []
        if self.vscode:
            resolved_folders.extend(_resolve_vscode_folder(self.vscode))
        return resolved_folders


class Projects(RootModel[Dict[project_key, Union[RepositoryProject, UserProject]]]):
    """
    Represents a collection of projects in the devcontainer configuration.

    This model manages multiple projects, including repository projects (root and ref)
    and user projects. It provides validation to ensure proper project structure
    and methods to resolve project folders for VSCode configuration.

    The model supports two types of projects:
    - RepositoryProject: For root and reference projects that are part of the repository
    - UserProject: For additional user-defined projects with custom paths and VSCode
                   configurations.

    Attributes:
        root (Dict[project_key, Union[RepositoryProject, UserProject]]): A dictionary
            mapping project keys to project instances. Keys can be reserved values
            like 'root' and 'ref' for repository projects, or custom identifiers
            for user projects.

    Validation Rules:
        - At least one project must be specified
        - If key is 'root', value must be a RepositoryProject instance
        - If key is 'ref', value must be a RepositoryProject instance
        - There can be at most one root project and one ref project

    Examples:
        >>> # Repository projects only
        >>> projects = Projects({
        ...     "root": RepositoryProject(path="/workspace"),
        ...     "ref": RepositoryProject(path="/workspace/ref")
        ... })

        >>> # Mixed repository and user projects
        >>> projects = Projects({
        ...     "root": RepositoryProject(path="/workspace"),
        ...     "my-project": UserProject(
        ...         path="/workspace/my-project",
        ...         alias="python-project"
        ...     )
        ... })
    """

    @model_validator(mode="after")
    def check_unique_root_and_ref_projects(self):
        """
        Validate that projects follow the required structure and constraints.

        This validator ensures that:
        1. At least one project is specified
        2. Root and ref projects are properly typed as RepositoryProject instances
        3. The project structure follows the expected conventions

        Raises:
            ValueError: If validation fails, with a descriptive error message
                explaining what constraint was violated.

        Returns:
            Projects: The validated Projects instance

        Examples:
            >>> # Valid configuration
            >>> projects = Projects({
            ...     "root": RepositoryProject(path="/workspace")
            ... })
            >>> validated = projects.check_unique_root_and_ref_projects()

            >>> # Invalid - no projects
            >>> projects = Projects({})
            >>> # Raises: ValueError("At least one project must be specified")

            >>> # Invalid - wrong type for root
            >>> projects = Projects({
            ...     "root": UserProject(path="/workspace")
            ... })
            >>> # Raises: ValueError(
            ...     "The value for key 'root' must be a RepositoryProject instance."
            ... )
        """
        if len(self.root.keys()) == 0:
            raise ValueError("At least one project must be specified")

        for key, value in self.root.items():
            if key == ReservedProjectKey.ROOT:
                if not isinstance(value, RepositoryProject):
                    raise ValueError(
                        f"The value for key '{ReservedProjectKey.ROOT.value}' must be "
                        "a RepositoryProject instance."
                    )

            if key == ReservedProjectKey.REF:
                if not isinstance(value, RepositoryProject):
                    raise ValueError(
                        f"The value for key '{ReservedProjectKey.REF.value}' must be "
                        "a RepositoryProject instance."
                    )

        return self

    def resolve_project_variables(self) -> Dict[str, Optional[ResolvedVariables]]:
        """
        Resolve all project variables to a dictionary mapping project identifiers to
        variables.
        """
        resolved_variables: Dict[str, Optional[ResolvedVariables]] = {}
        ref_project = self.root.get(ReservedProjectKey.REF, None)
        if ref_project:
            ref_variables = ref_project.variables
        else:
            ref_variables = None
        for key, value in self.root.items():
            if isinstance(value, UserProject):
                if not value.variables:
                    continue
                current_working_directory = pathlib.Path(value.path) / key
                key = value.alias if value.alias else key
                if ref_variables:
                    value.variables.root.update(ref_variables.root)
                resolved_variables[key] = value.variables.resolve(
                    current_working_directory
                )
            elif isinstance(value, RepositoryProject):
                if key == ReservedProjectKey.REF:
                    continue
                if not value.variables:
                    continue
                resolved_variables[key] = (
                    value.variables.resolve() if value.variables else None
                )
        return resolved_variables

    def resolve_project_folders(self) -> Dict[str, List[ResolvedFolder]]:
        """
        Resolve all projects to a dictionary mapping project identifiers to resolved
        folders.

        This method processes all projects in the collection and returns a dictionary
        where each key is a project identifier and each value is a list of
        ResolvedFolder objects representing the VSCode configuration files to be created
        for that project.

        For UserProject instances, the method:
        - Resolves the project's VSCode configuration
        - Adjusts destination paths to include the project path and key
        - Uses the project's alias as the key if available, otherwise uses the original
          key

        For RepositoryProject instances, the method:
        - Directly resolves the project's folders without path adjustments

        Returns:
            Dict[str, List[ResolvedFolder]]: A dictionary mapping project identifiers
                to lists of resolved folders. Each ResolvedFolder contains the
                destination path and source files for VSCode configuration.

        Examples:
            >>> projects = Projects({
            ...     "root": RepositoryProject(path="/workspace"),
            ...     "my-project": UserProject(
            ...         path="/workspace",
            ...         alias="python-project",
            ...         vscode=VSCodeFolder(
            ...             settings=[Folder({"python": [File("base")]})]
            ...         )
            ...     )
            ... })
            >>> resolved = projects.resolve_project_folders()
            # Returns:
            # {
            #     "root": [ResolvedFolder(
            #         destination=".vscode/settings.json",
            #         sources=[...]
            #     )],
            #     "python-project": [
            #         ResolvedFolder(
            #             destination="/workspace/my-project/.vscode/settings.json",
            #             sources=[...]
            #         )]
            # }
        """
        resolved_projects: Dict[str, List[ResolvedFolder]] = {}
        for key, value in self.root.items():
            if isinstance(value, UserProject):
                resolved_folders = value.resolve_folders()
                for resolved_folder in resolved_folders:
                    resolved_folder.destination = str(
                        pathlib.Path(value.path, key, resolved_folder.destination)
                    )
                key = value.alias if value.alias else key
                resolved_projects[key] = resolved_folders
            elif isinstance(value, RepositoryProject):
                resolved_projects[key] = value.resolve_folders()
        return resolved_projects
