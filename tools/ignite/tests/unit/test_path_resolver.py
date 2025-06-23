import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ignite.models.fs import ReservedFileName
from ignite.resolvers import PathResolver

@pytest.fixture()
def repository_context():
    return Path("files")

class TestPathResolver:
    """Test cases for PathResolver class."""

    def test_init(self, repository_context, user_context):
        """Test PathResolver initialization."""
        resolver = PathResolver(repository_context, user_context)
        
        assert resolver._PathResolver__repository_context == repository_context
        assert resolver._PathResolver__user_context == user_context

    def test_resolve_simple_file_in_repository(self, repository_context, user_context, tmp_path):
        """Test resolving a simple file that exists in repository context."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        path = Path("vscode") / "settings" / "python" / "base"
        paths = [path]
        result = resolver.resolve(paths)
        
        assert len(result) == 1
        assert result[0] == repository_context / "vscode" / "settings" / "python" / "base.json"

    def test_resolve_simple_file_in_user_context(self, repository_context, user_context):
        """Test resolving a simple file that exists in user context."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        # Create test file in user context
        user_file = user_context / "test.txt"
        user_file.write_text("user content")
        
        paths = [Path(".test")]
        result = resolver.resolve(paths)
        
        assert len(result) == 1
        assert result[0] == user_file

    def test_resolve_file_not_found(self, repository_context, user_context):
        """Test resolving a file that doesn't exist in either context."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        paths = [Path("nonexistent.txt")]
        
        with pytest.raises(FileNotFoundError, match="Can't find nonexistent.txt in repository or user context."):
            resolver.resolve(paths)

    def test_resolve_all_file_in_repository(self, repository_context, user_context, tmp_path):
        """Test resolving $all file in repository context."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        path = Path("vscode") / "settings" / "python" / ReservedFileName.ALL
        
        paths = [path]
        result = resolver.resolve(paths)
        
        assert len(result) > 0

    def test_resolve_with_ref_paths(self, repository_context, user_context):
        """Test resolving paths with reference paths."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        path = Path("vscode") / "settings" / "python" / ReservedFileName.REF.value        
        ref_paths = [Path("vscode") / "settings" / "python" / "base"]
        paths = [path]
        
        result = resolver.resolve(paths, ref_paths)
        
        assert len(result) == 1
        assert result[0] == repository_context / "vscode" / "settings" / "python" / "base.json"

    def test_resolve_with_ref_paths_no_match(self, repository_context, user_context):
        """Test resolving with ref paths that don't match."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        path = Path("vscode") / "settings" / "python" / ReservedFileName.REF.value        
        ref_paths = [Path("vscode") / "settings" / "nothing"]
        paths = [path]
        
        result = resolver.resolve(paths, ref_paths)
        
        assert len(result) == 0

    def test_resolve_multiple_paths(self, repository_context, user_context):
        """Test resolving multiple paths simultaneously."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        repo_file = Path("vscode") / "settings" / "python" / "base"
        user_file = user_context / "user.txt"
        user_file.write_text("user content")
        
        paths = [repo_file, Path(".user")]
        result = resolver.resolve(paths)
        
        assert len(result) == 2
        assert result[0] == repository_context / "vscode" / "settings" / "python" / "base.json"
        assert result[1] == user_context / "user.txt"

    def test_resolve_path_method_found(self, repository_context, user_context):
        """Test _resolve_path method when file is found."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        test_dir = repository_context / "vscode" / "settings" / "python"
        
        result = resolver._resolve_path(test_dir, "base")
        
        assert result == test_dir / "base.json"

    def test_resolve_path_method_not_found(self, repository_context, user_context):
        """Test _resolve_path method when file is not found."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        test_dir = repository_context / "vscode" / "settings" / "python"
        
        result = resolver._resolve_path(test_dir, "not_exist")
        
        assert result is None

    def test_resolve_all_file_method(self, repository_context, user_context):
        """Test _resolve_all_file method."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        test_dir = repository_context / "vscode" / "settings" / "python"
        
        result = resolver._resolve_all_file(test_dir)
        
        assert len(result) > 0

    def test_resolve_ref_method(self, repository_context, user_context):
        """Test _resolve_ref method."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        ref_paths = [Path("base")]
        paths = [Path(ReservedFileName.REF)]
        
        resolver._resolve_ref(ref_paths, paths)
        
        # The $ref should be replaced with matching ref_paths
        assert len(paths) == 1
        assert paths[0] == Path("base")

    def test_resolve_ref_file_method(self, repository_context, user_context):
        """Test _resolve_ref_file method."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        ref_paths = [Path("base")]
        ref_file = Path(ReservedFileName.REF)
        
        result = resolver._resolve_ref_file(ref_paths, ref_file)
        
        assert len(result) == 1
        assert result[0] == Path("base")

    def test_resolve_ref_file_method_no_matches(self, repository_context, user_context):
        """Test _resolve_ref_file method with no matching paths."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        ref_paths = [Path("vscode") / "settings" / "python" / "base"]
        ref_file = Path("vscode") / "tasks" / "base"
        
        result = resolver._resolve_ref_file(ref_paths, ref_file)
        
        assert len(result) == 0

    def test_resolve_with_mixed_file_types(self, repository_context, user_context):
        """Test resolving mixed file types (repository, user, $all, $ref)."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        # Setup test files
        repo_file = repository_context / "vscode" / "settings" / "python" / "base"
        
        user_file = user_context / "user.txt"
        user_file.write_text("user content")
        
        ref_paths = [Path("vscode") / "settings" / "python" / "base"]
        
        paths = [
            Path(".user"),
            Path("vscode") / "settings" / ReservedFileName.ALL,
            Path("vscode") / "settings" / "python" / ReservedFileName.REF
        ]
        
        result = resolver.resolve(paths, ref_paths)
        
        assert len(result) == 4
        assert result[0] == user_file
        assert result[1] == repository_context / "vscode" / "settings" / "coverage-gutters.json"
        assert result[2] == repository_context / "vscode" / "settings" / "on-save.json"
        assert result[3] == repository_context / "vscode" / "settings" / "python" / "base.json"

    def test_resolve_empty_paths_list(self, repository_context, user_context):
        """Test resolving an empty list of paths."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        result = resolver.resolve([])
        
        assert result == []

    def test_resolve_none_ref_paths(self, repository_context, user_context):
        """Test resolving with None ref_paths."""
        resolver = PathResolver(repository_context=repository_context, user_context=user_context)
        
        paths = [Path("test.txt")]
        
        # Should not raise an error
        with pytest.raises(FileNotFoundError):
            resolver.resolve(paths, None)
