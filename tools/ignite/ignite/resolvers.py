from pathlib import Path
from typing import List, Optional

from ignite.models.fs import ReservedFileName


class PathResolver:
    """
    A resolver for handling file paths with support for repository and user contexts.

    This class provides functionality to resolve file paths by searching in both
    repository and user contexts, with support for special file patterns like
    $all (all files in a directory) and $ref (reference to other paths).
    """

    def __init__(self, repository_context: Path, user_context: Path):
        """
        Initialize the PathResolver with repository and user contexts.

        Args:
            repository_context (Path): The base path for repository context files
            user_context (Path): The base path for user context files
        """
        self.__repository_context: Path = repository_context
        self.__user_context: Path = user_context

    @property
    def user_context(self) -> Path:
        return self.__user_context

    def resolve(
        self, paths: List[Path], ref_paths: Optional[List[Path]] = None
    ) -> List[Path]:
        """
        Resolve a list of paths to actual file locations.

        This method processes each path in the input list and resolves it to
        actual file locations by searching in the repository context first,
        then in the user context. It handles special patterns like $all and $ref.

        Args:
            paths (List[Path]): List of paths to resolve
            ref_paths (Optional[List[Path]]): Reference paths for $ref resolution.
                If None, no reference resolution is performed.

        Returns:
            List[Path]: List of resolved file paths

        Raises:
            FileNotFoundError: If a path cannot be resolved in either repository
                or user context
        """
        resolved_paths = []

        if ref_paths:
            paths = self._resolve_ref(ref_paths, paths)

        for path in paths:
            repository_path = Path(self.__repository_context, path.parent)
            if path.name == ReservedFileName.ALL:
                resolved_paths.extend(self._resolve_all_file(repository_path))
                continue

            repository_file = self._resolve_path(repository_path, path.stem)
            if repository_file:
                resolved_paths.append(repository_file)
                continue

            user_path = Path(self.__user_context, path.parent)
            user_file_stem = path.stem.removeprefix(".")
            user_file = self._resolve_path(user_path, user_file_stem)
            if user_file:
                resolved_paths.append(user_file)
                continue

            raise FileNotFoundError(f"Can't find {path} in repository or user context.")

        return resolved_paths

    def _resolve_path(self, path: Path, filename: str) -> Optional[Path]:
        """
        Find a file with the given filename in the specified directory.

        Args:
            path (Path): Directory to search in
            filename (str): Name of the file to find (without extension)

        Returns:
            Optional[Path]: Path to the found file, or None if not found
        """
        for file in path.iterdir():
            if file.is_file and file.stem == filename:
                return file
        return None

    def _resolve_all_file(self, path: Path) -> List[Path]:
        """
        Get all files in the specified directory.

        Args:
            path (Path): Directory to search for files

        Returns:
            List[Path]: List of all files found in the directory
        """
        resolved_paths = []
        for file in path.iterdir():
            if file.is_file():
                resolved_paths.append(file)
                continue
        return resolved_paths

    def _resolve_ref(self, ref_paths: List[Path], paths: List[Path]) -> List[Path]:
        """
        Resolve $ref patterns in the paths list by replacing them with matching
        reference paths.

        This method modifies the paths list in-place by replacing any $ref
        entries with the corresponding reference paths that have matching
        parent directories.

        Args:
            ref_paths (List[Path]): List of reference paths to use for resolution
            paths (List[Path]): List of paths that may contain $ref patterns.
                This list is modified in-place.
        """
        resolved_paths = []
        for path in paths:
            if path.name == ReservedFileName.REF:
                resolved_ref_paths = self._resolve_ref_file(ref_paths, path)
                for resolved_ref_path in resolved_ref_paths:
                    if resolved_ref_path in resolved_paths:
                        continue
                    resolved_paths.append(resolved_ref_path)
            else:
                resolved_paths.append(path)
        return resolved_paths

    def _resolve_ref_file(self, ref_paths: List[Path], ref_file: Path) -> List[Path]:
        """
        Find reference paths that match the parent directory of the reference file.

        Args:
            ref_paths (List[Path]): List of reference paths to search through
            ref_file (Path): Reference file path whose parent directory is used
                for matching

        Returns:
            List[Path]: List of reference paths that have the same parent
                directory as the reference file
        """
        paths = []
        ref_base_path = ref_file.parent
        for ref_path in ref_paths:
            if ref_path.is_relative_to(ref_base_path):
                paths.append(ref_path)
        return paths
