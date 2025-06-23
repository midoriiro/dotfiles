from pathlib import Path
from typing import Dict, List, Optional, Union, override
from pydantic import BaseModel, Field, model_validator

from ignite.models.fs import File, Folder, ResolvedFolder

class BaseFolder(BaseModel):
    """
    Base class for folder-like structures that can be resolved to a list of ResolvedFolder objects.
    
    This abstract base class provides the foundation for folder structures that need to be
    processed and converted into ResolvedFolder objects. It defines the interface that all
    folder implementations must follow and provides common utility methods for resolving
    folder contents.
    
    The class is designed to be inherited by specific folder implementations (like VSCodeFolder)
    that provide concrete implementations of the resolve() method. It also includes a utility
    method for processing mixed lists of Folder and File objects.
    
    Attributes:
        Inherits all attributes from Pydantic's BaseModel
    
    Methods:
        resolve(): Abstract method that must be implemented by subclasses
        _resolve_folder(): Utility method for processing folder/file lists
    
    Examples:
        This class is not meant to be instantiated directly. Instead, use concrete
        implementations like VSCodeFolder:
        
        >>> vscode = VSCodeFolder(settings=[...], tasks=[...])
        >>> resolved = vscode.resolve()
    
    Note:
        - This is an abstract base class that cannot be instantiated directly
        - Subclasses must implement the resolve() method
        - The _resolve_folder() method is provided as a utility for common operations
        - All folder implementations should inherit from this class for consistency
    """

    def resolve(self) -> List[ResolvedFolder]:
        """
        Resolve the folder structure to a list of ResolvedFolder objects.
        
        This abstract method must be implemented by subclasses to define how the
        specific folder type should be processed and converted into ResolvedFolder
        objects. The implementation should handle the folder's specific structure
        and return the appropriate list of resolved folders.
        
        Returns:
            List[ResolvedFolder]: A list of ResolvedFolder objects representing
                the resolved folder structure. The exact content depends on the
                specific implementation.
                
        Raises:
            NotImplementedError: Always raised when called on the base class.
                Subclasses must provide their own implementation.
                
        Examples:
            In a concrete implementation, this method would process the folder's
            contents and return appropriate ResolvedFolder objects:
            
            >>> class MyFolder(BaseFolder):
            ...     def resolve(self) -> List[ResolvedFolder]:
            ...         # Implementation specific to MyFolder
            ...         return [ResolvedFolder(sources=[...], destination="...")]
        """
        raise NotImplementedError("Subclass must implement this method.")
    
    def _resolve_folder(self, folder: List[Union[Folder, File]]) -> List[Path]:
        """
        Resolve a list of folders and files to a list of file paths.
        
        This utility method processes a mixed list of Folder and File objects and
        converts them into a flat list of file paths. It handles the recursive
        resolution of nested folders and the direct conversion of files to paths.
        
        Args:
            folder (List[Union[Folder, File]]): A list containing Folder and/or File
                objects to be resolved. The list can contain any combination of
                these types, and folders can be nested at any depth.
                
        Returns:
            List[Path]: A flat list of file paths representing all files found
                in the folder structure. Each path represents a single file that
                was either directly specified as a File object or found within
                nested Folder objects.
                
        Examples:
            Basic usage with mixed content:
            >>> base = BaseFolder()
            >>> files = [File("config.json"), Folder({"src": [File("main.py")]})]
            >>> paths = base._resolve_folder(files)
            >>> # Returns: [Path("config.json"), Path("src/main.py")]
            
            Usage with nested folders:
            >>> nested = [
            ...     Folder({"settings": [File("base.json")]}),
            ...     Folder({"tasks": [File("build.json")]})
            ... ]
            >>> paths = base._resolve_folder(nested)
            >>> # Returns: [Path("settings/base.json"), Path("tasks/build.json")]
            
        Note:
            - This method recursively processes nested folder structures
            - File objects are converted to Path objects using their root attribute
            - Folder objects are processed by calling their resolve() method
            - The resulting list contains only file paths, not folder paths
            - The order of paths in the result follows the order of items in the input list
        """
        paths = []
        for item in folder:
            if isinstance(item, Folder):
                paths.extend(item.resolve())
            elif isinstance(item, File):
                paths.append(Path(item.root))
        return paths

class VSCodeFolder(BaseFolder):
    """
    Represents a VSCode folder configuration for settings and tasks.
    
    This class manages the organization and resolution of VSCode configuration files,
    specifically handling settings.json and tasks.json files. It provides a structured
    way to organize multiple configuration sources that will be merged into the final
    VSCode configuration files.
    
    Attributes:
        settings (Optional[List[Union[Folder, File]]]): 
            A list of Folder and/or File objects representing VSCode settings
            configuration sources. These will be merged into a single settings.json
            file. Can be None if no settings are configured.
            
        tasks (Optional[List[Union[Folder, File]]]): 
            A list of Folder and/or File objects representing VSCode tasks
            configuration sources. These will be merged into a single tasks.json
            file. Can be None if no tasks are configured.
    
    Validation Rules:
        - settings can be None or a non-empty list of Folder/File objects
        - tasks can be None or a non-empty list of Folder/File objects
        - Both settings and tasks are optional
        - Empty lists are not allowed for either settings or tasks
    
    Examples:
        Basic usage with settings only:
        >>> settings_folder = Folder({"python": [File("base"), File("black")]})
        >>> vscode = VSCodeFolder(settings=[settings_folder])
        >>> resolved = vscode.resolve()
        >>> # Returns: [ResolvedFolder with settings.json destination]
        
        Usage with both settings and tasks:
        >>> settings_folder = Folder({"python": [File("base")]})
        >>> tasks_folder = Folder({"poetry": [File("build")]})
        >>> vscode = VSCodeFolder(
        ...     settings=[settings_folder],
        ...     tasks=[tasks_folder]
        ... )
        >>> resolved = vscode.resolve()
        >>> # Returns: [ResolvedFolder for settings.json, ResolvedFolder for tasks.json]
        
        Usage with direct files:
        >>> vscode = VSCodeFolder(
        ...     settings=[File("base")],
        ...     tasks=[File("build")]
        ... )
        >>> resolved = vscode.resolve()
        >>> # Returns: [ResolvedFolder for settings.json, ResolvedFolder for tasks.json]
    
    Note:
        - Settings sources are prefixed with "settings/" in the resolved paths
        - Tasks sources are prefixed with "tasks/" in the resolved paths
        - The final output will be two separate ResolvedFolder objects if both
          settings and tasks are configured
        - Empty or None values for settings/tasks will be ignored
        - Each ResolvedFolder represents a separate configuration file
    """

    settings: Optional[List[Union[Folder, File]]] = Field(
        None, description="List of VSCode settings configuration sources"
    )
    tasks: Optional[List[Union[Folder, File]]] = Field(
        None, description="List of VSCode tasks configuration sources"
    )

    @model_validator(mode="after")
    def validate_settings_and_tasks(self):
        """
        Validate that settings and tasks are properly configured.
        
        This validator ensures that if settings or tasks are provided, they are
        not empty lists. Empty lists are not allowed as they would result in
        no configuration being generated.
        
        Returns:
            self: The validated VSCodeFolder instance
            
        Raises:
            ValueError: If settings or tasks is an empty list
        """
        if self.settings is not None and len(self.settings) == 0:
            raise ValueError("settings must be a non-empty list")
        if self.tasks is not None and len(self.tasks) == 0:
            raise ValueError("tasks must be a non-empty list")
        return self

    @override
    def resolve(self) -> List[ResolvedFolder]:
        """
        Resolve the VSCode folder configuration to a list of ResolvedFolder objects.
        
        This method processes the settings and tasks configurations, converting them
        into ResolvedFolder objects that represent the final VSCode configuration
        files to be generated. Each ResolvedFolder contains the source paths and
        destination file information needed for file merging operations.
        
        Returns:
            List[ResolvedFolder]: A list of ResolvedFolder objects representing
                the VSCode configuration files to be generated. The list will contain:
                - One ResolvedFolder for settings.json if settings are configured
                - One ResolvedFolder for tasks.json if tasks are configured
                - Empty list if neither settings nor tasks are configured
        
        Examples:
            Basic resolution with settings:
            >>> settings_folder = Folder({"python": [File("base")]})
            >>> vscode = VSCodeFolder(settings=[settings_folder])
            >>> resolved = vscode.resolve()
            >>> # Returns: [ResolvedFolder(sources=["settings/python/base"], destination="settings.json")]
            
            Resolution with both configurations:
            >>> vscode = VSCodeFolder(
            ...     settings=[Folder({"python": [File("base")]})],
            ...     tasks=[Folder({"poetry": [File("build")]})]
            ... )
            >>> resolved = vscode.resolve()
            >>> # Returns: [
            ... #   ResolvedFolder(sources=["settings/python/base"], destination="settings.json"),
            ... #   ResolvedFolder(sources=["tasks/poetry/build"], destination="tasks.json")
            ... # ]
            
            Resolution with no configuration:
            >>> vscode = VSCodeFolder()
            >>> resolved = vscode.resolve()
            >>> # Returns: []
        
        Note:
            - Settings sources are prefixed with "settings/" path
            - Tasks sources are prefixed with "tasks/" path
            - Source paths are converted to strings for ResolvedFolder compatibility
            - The method handles None values gracefully by skipping them
            - Each ResolvedFolder represents a separate configuration file
            - The order of ResolvedFolder objects is: settings first, then tasks
        """
        resolved_folders: List[ResolvedFolder] = []
        
        # Process settings configuration
        if self.settings:
            sources = []
            base_settings_path = Path("settings")
            for source in self._resolve_folder(self.settings):
                sources.append(str(Path(base_settings_path, source)))
            resolved_folders.append(ResolvedFolder.model_construct(
                sources=sources,
                destination="settings.json"
            ))
        
        # Process tasks configuration
        if self.tasks:
            sources = []
            base_tasks_path = Path("tasks")
            for source in self._resolve_folder(self.tasks):
                sources.append(str(Path(base_tasks_path, source)))
            resolved_folders.append(ResolvedFolder.model_construct(
                sources=sources,
                destination="tasks.json"
            ))
        
        return resolved_folders

        
