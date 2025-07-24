import pathlib
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ignite.models.fs import Path, ResolvedFolder
from ignite.models.policies import Policies
from ignite.models.projects import (
    Projects,
    RepositoryProject,
    ReservedProjectKey,
    UserProject,
)
from ignite.models.variables import ResolvedVariables, Variables
from ignite.resolvers import PathResolver


class WorkspaceFolderSpecification(BaseModel):
    """
    Represents a folder specification in a workspace file.

    This model defines the structure for individual folders within a workspace,
    including their path and optional display name.

    Attributes:
        path: The absolute or relative path to the folder within the workspace.
              This can be a string path that will be resolved relative to the
              workspace root.
        name: Optional display name for the folder. If not provided, the folder
              will be displayed using its path. This is useful for providing
              more user-friendly names in the IDE.
    """

    path: Path = Field(..., description="The path of the folder")
    name: Optional[str] = Field(None, description="The name of the folder")


class WorkspaceFileSpecification(BaseModel):
    """
    Represents a workspace file specification for VS Code.

    This model defines the structure for a VS Code workspace file (.code-workspace),
    which contains the configuration for a multi-root workspace including folder
    specifications and workspace-level settings.

    Attributes:
        folders: A list of folder specifications that define the projects and
                directories included in the workspace. Each folder can have a
                path and optional display name.
        settings: A dictionary containing workspace-level settings that apply
                 to all folders in the workspace. These settings override
                 user settings but can be overridden by folder-specific settings.
                 Defaults to an empty dictionary if no settings are provided.
    """

    folders: List[WorkspaceFolderSpecification] = Field(
        ..., description="The folders in the file"
    )
    settings: Dict[str, Any] = Field(
        ..., description="The settings in the file", default_factory=dict
    )


class Workspace(BaseModel):
    """
    Represents a workspace configuration for development environments.

    This model defines the structure and behavior of a workspace, including
    the policies that govern how the workspace operates and the projects
    that are contained within it. The workspace serves as the top-level
    configuration that orchestrates multiple projects and their interactions.

    Attributes:
        policies: The policies that define the behavior and rules for the
                 workspace. These include container policies, folder creation
                 policies, file write policies, and other operational rules
                 that govern how the workspace functions.
        projects: The collection of projects within the workspace. This can
                 include user-defined projects, repository projects, and
                 special reference projects that provide shared resources
                 or configurations.

    Methods:
        resolve_project_folders: Resolves all project folders in the workspace,
                                applying path resolution and reference project
                                handling to create a complete folder structure.
        resolve_file_specification: Creates a VS Code workspace file specification
                                   that defines the folder structure and settings
                                   for the workspace.
    """

    policies: Policies = Field(..., description="The policies for the workspace")
    projects: Projects = Field(..., description="The projects in the workspace")

    def resolve_project_variables(self) -> Dict[str, ResolvedVariables]:
        """
        Resolve all project variables to a dictionary mapping project identifiers to variables.
        """
        resolved_variables: Dict[str, Variables] = {}
        for (
            project_name,
            variables,
        ) in self.projects.resolve_project_variables().items():
            if variables:
                resolved_variables[project_name] = variables
        return resolved_variables

    def resolve_project_folders(
        self, path_resolver: PathResolver
    ) -> Dict[str, List[ResolvedFolder]]:
        """
        Resolve all project folders in the workspace using the provided path resolver.

        This method processes all projects in the workspace, resolves their folder
        structures, and handles special reference projects that provide shared
        resources. It applies path resolution to ensure all folder paths are
        correctly resolved relative to the workspace structure.

        Args:
            path_resolver: The path resolver instance used to resolve relative
                          paths and handle path transformations.

        Returns:
            A dictionary mapping project names to lists of resolved folders.
            Each resolved folder contains the final path information after
            resolution and any necessary transformations.

        Note:
            Reference projects (ReservedProjectKey.REF) are processed first and
            their paths are used as reference points for resolving other project
            paths. The reference project itself is not included in the final
            result as it serves only as a reference for path resolution.
        """
        resolved_folders: Dict[str, List[ResolvedFolder]] = {}
        for (
            project_name,
            project_resolved_folders,
        ) in self.projects.resolve_project_folders().items():
            resolved_folders[project_name] = project_resolved_folders
        ref_project = resolved_folders.get(ReservedProjectKey.REF, None)
        if ref_project:
            del resolved_folders[ReservedProjectKey.REF]
            ref_paths = [
                pathlib.Path(resolved_folder)
                for resolved_folders in ref_project
                for resolved_folder in resolved_folders.sources
            ]
        else:
            ref_paths = None
        for project_name, project_resolved_folders in resolved_folders.items():
            for resolved_folder in project_resolved_folders:
                paths = [pathlib.Path(source) for source in resolved_folder.sources]
                resolved_folder.sources = path_resolver.resolve(paths, ref_paths)
        return resolved_folders

    def resolve_file_specification(self) -> WorkspaceFileSpecification:
        """
        Create a VS Code workspace file specification from the workspace configuration.

        This method generates a workspace file specification that defines the
        folder structure and settings for a VS Code multi-root workspace. It
        processes all projects in the workspace and creates appropriate folder
        specifications based on the project type.

        For UserProject instances, it creates folder specifications with the
        project path and an optional display name (using the project alias if
        available, otherwise the project name). For RepositoryProject instances
        with the ROOT key, it creates a folder specification pointing to the
        current directory (".").

        Returns:
            A WorkspaceFileSpecification containing the folder structure and
            settings for the VS Code workspace file. The folders list contains
            WorkspaceFolderSpecification instances for each project, and the
            settings dictionary contains workspace-level settings (currently
            empty but can be extended for workspace-specific configurations).

        Note:
            Only UserProject and RepositoryProject (with ROOT key) instances
            are included in the workspace file specification. Other project
            types or special projects are excluded from the workspace file.
        """
        workspace_file_specification: WorkspaceFileSpecification = (
            WorkspaceFileSpecification(folders=[], settings={})
        )
        for project_name, project in self.projects.root.items():
            if isinstance(project, UserProject):
                workspace_file_specification.folders.append(
                    WorkspaceFolderSpecification(
                        path=str(pathlib.Path(project.path, project_name)),
                        name=project.alias if project.alias else project_name,
                    )
                )
            elif (
                isinstance(project, RepositoryProject)
                and project_name == ReservedProjectKey.ROOT
            ):
                workspace_file_specification.folders.append(
                    WorkspaceFolderSpecification(
                        path=".",
                    )
                )
        return workspace_file_specification
