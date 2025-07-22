import pathlib
from enum import Enum
from typing import Annotated, Callable, Dict, List, Literal, Union

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    RootModel,
    StringConstraints,
    model_validator,
)

from ignite.mergers import FileMerger, IniFileMerger, JsonFileMerger, YamlFileMerger
from ignite.models.common import Identifier, IdentifierPattern


class ReservedFileName(str, Enum):
    REF = "$ref"
    ALL = "$all"


UserFile = Annotated[
    str,
    StringConstraints(
        min_length=2, max_length=256, pattern=rf"^\.{IdentifierPattern}$"
    ),
]
RefFile = Literal[ReservedFileName.REF]
AllFile = Literal[ReservedFileName.ALL]
RepositoryFile = Identifier


UnixAbsolutePath = Annotated[
    str,
    StringConstraints(
        pattern=r"^/([^/@#$%&*+=?!|~`'\"()\[\]{}<>;:,]+(/)?)*$",
        min_length=1,
        max_length=256,
    ),
]

WindowsAbsolutePath = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-Za-z]:(\\|/)([^/@#$%&*+=?!|~`'\"()\[\]{}<>;:,]+(\\|/)?)*$",
        min_length=1,
        max_length=256,
    ),
]

AbsolutePath = Union[UnixAbsolutePath, WindowsAbsolutePath]


def validate_relative_path(value: str) -> str:
    """Validate that relative path is not whitespace-only."""
    if value.strip() == "":
        raise ValueError("Path cannot be whitespace-only")
    return value


RelativePath = Annotated[
    str,
    BeforeValidator(validate_relative_path),
    StringConstraints(
        pattern=r"^([^/@#$%&*+=?!|~`'\"()\[\]{}<>;:,]+(/)?)*$",
        min_length=1,
        max_length=256,
    ),
]

Path = Union[AbsolutePath, RelativePath]


class FileTemplateVariables(BaseModel):
    """
    A model that represents variables used for resolving placeholders in file templates.

    This class provides functionality to replace template variables with actual values,
    currently supporting project name substitution in template strings. It is designed
    to work with file templates that contain variable placeholders in the format
    ${variable-name}.

    Attributes:
        project_name (str):
            The name of the project. This value will be used to replace the
            ${project-name} placeholder in template strings. Must be between 1 and
            50 characters long.

    Example:
        >>> variables = FileTemplateVariables(project_name="my-awesome-project")
        >>> result = variables.resolve("Welcome to ${project-name}!")
        >>> print(result)
        'Welcome to my-awesome-project!'

    Validation Rules:
        - project_name must be a non-empty string
        - project_name must be between 1 and 50 characters long
        - project_name can contain letters, numbers, hyphens, and underscores

    Supported Template Variables:
        - ${project-name}: Replaced with the project_name value

    Usage:
        This class is typically used in conjunction with file generation systems
        where templates need to be customized with project-specific information.
        The resolve() method processes template strings and replaces all known
        variable placeholders with their corresponding values.
    """

    project_name: str = Field(
        ..., min_length=1, max_length=50, description="The name of the project."
    )

    def resolve(self, template: str) -> str:
        """
        Resolve template variables by replacing placeholders with actual values.

        This method processes a template string and replaces variable placeholders
        with their corresponding values from the FileTemplateVariables instance.
        Currently supports the ${project-name} variable which gets replaced with
        the project_name value.

        Args:
            template (str):
                The template string containing variable placeholders.
                Must not be None, empty, or whitespace-only.
                Example: "Hello ${project-name}!"

        Returns:
            str:
                The resolved template with all variables replaced with their values.
                Example: "Hello my-project!" if project_name is "my-project"

        Raises:
            ValueError:
                If the template is None, empty, or contains only whitespace.
                The error message will be "Template cannot be empty."

        Examples:
            >>> variables = FileTemplateVariables(project_name="my-app")
            >>> variables.resolve("Project: ${project-name}")
            'Project: my-app'

            >>> variables.resolve("No variables here")
            'No variables here'

        Note:
            - Variable replacement is case-sensitive
            - Multiple occurrences of the same variable are all replaced
            - If a variable placeholder doesn't match any known variables, it remains unchanged
            - The method preserves the original template structure and formatting
        """
        if not template or template.strip() == "":
            raise ValueError("Template cannot be empty.")
        resolved = template
        if self.project_name:
            resolved = resolved.replace("${project-name}", self.project_name)
        return resolved


class ResolvedFile(BaseModel):
    """
    Represents a resolved file with its final path and content.

    This class encapsulates a file that has been fully processed and resolved,
    containing both the destination path where the file should be written and
    the final content that should be written to that path.

    Attributes:
        path (Path):
            The destination path where the file should be written.
            This represents the final location of the file in the file system.
            Must be a valid file path.

        content (str):
            The final content that should be written to the file.
            This content has been fully processed and is ready for writing.
            Must not be None, but can be empty if the file should be empty.

    Validation Rules:
        - path must be a valid file path
        - content must be a string (can be empty)

    Examples:
        Basic usage:
        >>> file = ResolvedFile(
        ...     path=Path("output/config.json"),
        ...     content='{"key": "value"}'
        ... )

        Empty file:
        >>> file = ResolvedFile(
        ...     path=Path("output/.gitkeep"),
        ...     content=""
        ... )

    Note:
        - This class is typically used as the final output of file processing
        - The content should be ready for immediate writing to the file system
        - Both path and content are immutable once the object is created
        - The path should represent the complete destination path including filename
    """

    path: Path = Field(
        ..., description="The destination path where the file should be written."
    )
    content: str = Field(
        ...,
        min_length=1,
        description="The final content that should be written to the file.",
    )


class ResolvedFolder(BaseModel):
    """
    Represents a resolved folder that can merge multiple source files into a single destination file.

    This class is designed to handle the merging of multiple configuration files (JSON, YAML, INI)
    into a single output file while applying template variable substitution. It provides a
    unified interface for file merging operations regardless of the source file formats.

    Attributes:
        sources (List[Path]):
            A list of source file paths to be merged. Must contain at least one path.
            All source files should be of the same type (JSON, YAML, or INI) for proper merging.
            The files will be merged in the order they appear in this list.

        destination (Path):
            The destination path where the merged content will be written.
            The file extension determines the merger type and output format.
            Supported extensions: .json, .yaml, .yml, .ini

    Supported File Types:
        - JSON files (.json): Uses JsonFileMerger for merging JSON objects
        - YAML files (.yaml, .yml): Uses YamlFileMerger for merging YAML documents
        - INI files (.ini): Uses IniFileMerger for merging INI configuration files

    Validation Rules:
        - sources must contain at least one path (min_length=1)
        - destination must be a valid file path
        - All source files must exist and be readable
        - Source files must be of compatible types for merging

    Examples:
        Basic usage with JSON files:
        >>> folder = ResolvedFolder(
        ...     sources=[Path("config1.json"), Path("config2.json")],
        ...     destination=Path("merged.json")
        ... )

        Usage with YAML files:
        >>> folder = ResolvedFolder(
        ...     sources=[Path("base.yaml"), Path("override.yml")],
        ...     destination=Path("final.yaml")
        ... )

        Usage with template variables:
        >>> variables = FileTemplateVariables(project_name="my-project")
        >>> folder = ResolvedFolder(
        ...     sources=[Path("template.json")],
        ...     destination=Path("output.json")
        ... )
        >>> resolved = folder.resolve(variables)

    Error Handling:
        - Raises ValidationError if sources list is empty
        - Raises ValidationError if destination path is invalid
    """

    sources: List[Path] = Field(
        ...,
        min_length=1,
        description="List of source paths to merge. Must contain at least one path.",
    )
    destination: Path = Field(
        ...,
        description="The destination path where the merged content will be written.",
    )

    def resolve(self, variables: FileTemplateVariables) -> ResolvedFile:
        """
        Resolve the folder to a resolved file by merging source files and applying template variables.

        This method performs the following steps:
            1. Validates that variables are provided
            2. Determines the appropriate file merger based on the destination file extension
            3. Merges all source files into a single data structure
            4. Writes the merged data to a string representation
            5. Applies template variable substitution to the content
            6. Returns a ResolvedFile with the final path and content

        Args:
            variables (FileTemplateVariables):
                The template variables to apply to the resolved content.
                Cannot be None.

        Returns:
            ResolvedFile:
                A resolved file containing the destination path and processed content.
                The content will have all template variables replaced with their values.

        Raises:
            ValueError:
                If variables is None. The error message will be "Variables cannot be None."
                If the destination file extension is not supported. The error message will be
                "Unsupported file extension: {extension}" where {extension} is the actual extension.
                Supported extensions are: .json, .yaml, .yml, .ini

        Examples:
            >>> variables = FileTemplateVariables(project_name="my-project")
            >>> folder = ResolvedFolder(
            ...     sources=[Path("config1.json"), Path("config2.json")],
            ...     destination=Path("merged.json")
            ... )
            >>> resolved = folder.resolve(variables)
            >>> print(resolved.path)
            merged.json
            >>> print(resolved.content)
            {"project": "my-project", "merged": true}

        Note:
            - The method automatically selects the appropriate merger based on file extension
            - JSON files use JsonFileMerger
            - YAML files (.yaml or .yml) use YamlFileMerger
            - INI files use IniFileMerger
            - Template variable substitution is applied after merging and writing
            - The original source files are not modified during this process
        """
        if variables is None:
            raise ValueError("Variables cannot be None.")
        extension = pathlib.Path(self.destination).suffix
        merger: FileMerger = None
        if extension == ".json":
            merger = JsonFileMerger()
        elif extension in [".yaml", ".yml"]:
            merger = YamlFileMerger()
        elif extension == ".ini":
            merger = IniFileMerger()
        else:
            raise ValueError(f"Unsupported file extension: {extension}")
        data = merger.merge(self.sources)
        content = None

        def writer(x: str) -> None:
            nonlocal content
            content = x

        merger.write(data, writer)
        content = variables.resolve(content)
        return ResolvedFile(path=self.destination, content=content)


class File(RootModel[Union[RepositoryFile, UserFile, RefFile, AllFile]]):
    """
    Represents a file in the file system model.

    This model can hold a file name that represents different types of files:
        - :data:`RepositoryFile`: Regular files from the repository
        - :data:`UserFile`: User-specific files (starting with a dot)
        - :data:`RefFile`: Reference files (using the reserved keyword "$ref")
        - :data:`AllFile`: All files (using the reserved keyword "$all")

    The model uses Pydantic's RootModel to wrap a Union type, allowing it to accept
    any of the supported file types while maintaining type safety and validation.

    Examples:
        >>> # Repository file
        >>> file = File("config.json")
        >>> print(file.root)
        config.json

        >>> # User file
        >>> file = File(".env")
        >>> print(file.root)
        .env

        >>> # Reference file
        >>> file = File("$ref")
        >>> print(file.root)
        $ref

        >>> # All files
        >>> file = File("$all")
        >>> print(file.root)
        $all

    Note:
        - The model automatically validates the file type based on the input
        - Reserved keywords ("$ref", "$all") are case-sensitive and must match exactly
        - User files must start with a dot (.)
        - Repository files are any other valid file names
    """

    pass


class Folder(RootModel[Dict[Identifier, List[Union[File, "Folder"]]]]):
    """
    Represents a folder containing files and/or subfolders in the file system model.

    This model uses Pydantic's RootModel to wrap a dictionary where:
        - Keys are folder names (:data:`Identifier`)
        - Values are lists containing File objects and/or nested Folder objects

    The model implements comprehensive validation rules to ensure proper file system structure:

    Folder Validation Rules:
        - Folder names must be unique within the same level
        - Multiple folders are allowed, but with the above restrictions

    File Validation Rules:
        - Folder must contain at least one file
        - Reserved keywords have special validation:
            - "$all" cannot be defined more than once
            - "$ref" cannot be defined more than once
            - "$ref" and "$all" cannot be defined simultaneously
            - "$all" cannot be defined simultaneously with repository files
        - File names must be unique (excluding reserved keywords)
        - Files are categorized into:
            - Repository files: regular files (e.g., "config")
            - User files: files starting with a dot (e.g., ".env")
            - Reference files: using "$ref" keyword
            - All files: using "$all" keyword

    Structure:
        The model supports nested folder structures where each folder can contain:
        - Multiple files of different types
        - Multiple subfolders
        - A combination of files and subfolders

    Examples:
        >>> # Simple folder with files
        >>> folder = Folder({
        ...     "config": [File("config.json"), File(".env")]
        ... })

        >>> # Folder with subfolders
        >>> folder = Folder({
        ...     "src": [
        ...         File("main.py"),
        ...         Folder({"utils": [File("helper.py")]})
        ...     ]
        ... })

        >>> # Folder with reserved keywords
        >>> folder = Folder({
        ...     "data": [File("$ref"), File(".user_data.json")]
        ... })

        >>> # Complex nested structure with multiple levels
        >>> folder = Folder({
        ...     "src": [
        ...         File("main.py"),
        ...         File("$ref"),
        ...         Folder({
        ...             "utils": [
        ...                 File("helper.py"),
        ...                 File(".config"),
        ...                 Folder({
        ...                     "internal": [
        ...                         File("$all")
        ...                     ]
        ...                 })
        ...             ]
        ...         }),
        ...         Folder({
        ...             "tests": [
        ...                 File("test_main.py"),
        ...                 File(".test_config"),
        ...                 Folder({
        ...                     "unit": [File("test_utils.py")],
        ...                     "integration": [File("test_api.py")]
        ...                 })
        ...             ]
        ...         })
        ...     ],
        ...     "config": [
        ...         File("settings.json"),
        ...         File(".env"),
        ...         Folder({
        ...             "environments": [
        ...                 File("dev.json"),
        ...                 File("prod.json")
        ...             ]
        ...         })
        ...     ]
        ... })

    Note:
        - The model automatically validates all rules during instantiation
        - Reserved keywords are case-sensitive and must match exactly
        - The resolve() method can be used to get a flat list of all file paths
        - Validation errors provide clear messages about rule violations
    """

    @staticmethod
    def _validate_unique_folder_names(folders: List[Identifier]) -> None:
        unique_folders = list(set(folders))
        if len(unique_folders) != len(folders):
            raise ValueError(f"Folder names must be unique.")

    @model_validator(mode="after")
    def validate_folder_contents(self):
        filtered_items = [item for value in self.root.values() for item in value]

        folders = [item.root for item in filtered_items if isinstance(item, Folder)]

        if len(folders) > 1:
            folder_names = []
            for folder in folders:
                folder_names.extend(folder.keys())
            self._validate_unique_folder_names(folder_names)

        files = [item.root for item in filtered_items if isinstance(item, File)]

        if len(folders) == 0 and len(files) == 0:
            raise ValueError(f"Folder must contain at least one file or one subfolder.")

        all_files = []
        ref_files = []
        repository_files = []
        user_files = []
        for file in files:
            if file == ReservedFileName.REF:
                ref_files.append(file)
            elif file == ReservedFileName.ALL:
                all_files.append(file)
            elif file.startswith("."):
                user_files.append(file)
            else:
                repository_files.append(file)

        if len(all_files) > 1:
            raise ValueError(
                f"'{ReservedFileName.ALL.value}' cannot be defined more than once."
            )
        if len(ref_files) > 1:
            raise ValueError(
                f"{ReservedFileName.REF.value} cannot be defined more than once."
            )

        if len(all_files) == 1:
            all_file = all_files[0]
        else:
            all_file = None

        if len(ref_files) == 1:
            ref_file = ref_files[0]
        else:
            ref_file = None

        if ref_file and all_file:
            raise ValueError(
                f"'{ReservedFileName.REF.value}' and '{ReservedFileName.ALL.value}' cannot be defined simultaneously."
            )

        if all_file and len(repository_files) > 0:
            raise ValueError(
                f"'{ReservedFileName.ALL.value}' cannot be defined simultaneously with repository files."
            )

        user_and_repository_files = [item for item in repository_files + user_files]

        unique_files = list(set(user_and_repository_files))
        if len(unique_files) != len(user_and_repository_files):
            raise ValueError(f"File names must be unique.")

        return self

    def resolve(self) -> List[pathlib.Path]:
        """
        Resolve the folder structure to a list of absolute file paths.

        This method traverses the folder's root dictionary and recursively resolves
        all nested folders and files to their complete path representations.

        Returns:
            List[pathlib.Path]: A list of resolved file paths. Each path represents
                a file within the folder structure, with the folder's key as the
                base directory and the file's location as the relative path.

        Example:
            If the folder contains:
            {
                "src": [File("main"), Folder("nested", [File("file")])],
                "tests": [File("test_main")]
            }

            The method will return paths like:
            - pathlib.Path("src", "main")
            - pathlib.Path("src", "nested", "file")  # from nested folder
            - pathlib.Path("tests", "test_main")
        """
        paths = []
        for key, value in self.root.items():
            for item in value:
                if isinstance(item, Folder):
                    folder_paths = [pathlib.Path(key, path) for path in item.resolve()]
                    paths.extend(folder_paths)
                elif isinstance(item, File):
                    paths.append(pathlib.Path(key, item.root))
        return paths


Folder.model_rebuild()
