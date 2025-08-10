import os
import stat
import sys
from pathlib import Path
from typing import Any, Dict, Generator, Self, override

from _pytest._py.path import LocalPath

from poexy_core.utils.symbolic_link import SymbolicLink


def _transform_case_path_to_sample_path(test_path: Path, test_name: str) -> Path:
    for index, part in enumerate(test_path.parts):
        if part == "cases":
            test_path = (
                Path(*list(test_path.parts[:index]))
                / "samples"
                / Path(*list(test_path.parts[index + 1 :]))  # noqa: E203
            )
            break
    test_path = test_path / test_name.replace("test_", "")
    return test_path


class TestPath:
    __test__ = False

    def __init__(
        self,
        path: str,
    ):
        self._path = Path(path)
        self.__sample_path = None
        self.__sample_src_path = None
        self.__node_id = None

    def to_json(self) -> Dict[str, Any]:
        if self.__sample_path is None:
            raise ValueError("Sample path not set")
        if self.__sample_src_path is None:
            raise ValueError("Sample src path not set")
        if self.__node_id is None:
            raise ValueError("Node id not set")
        return {
            "type": self.__class__.__name__,
            "path": str(self._path),
            "sample_path": str(self.__sample_path),
            "sample_src_path": str(self.__sample_src_path),
            "node_id": self.__node_id,
        }

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> Self:
        cls_name = data["type"]
        module = sys.modules[__name__]
        cls: Self = getattr(module, cls_name)
        instance = object.__new__(cls)
        instance.from_json(data)
        return instance

    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        self._path = Path(data["path"])
        self.__sample_path = Path(data["sample_path"])
        self.__sample_src_path = Path(data["sample_src_path"])
        self.__node_id = data["node_id"]

    def _prefix(self, path: LocalPath) -> Path:
        if self.__sample_path is None:
            self.__sample_path = _transform_case_path_to_sample_path(
                Path(path.dirname), path.purebasename
            )
            sample_name = self.__sample_path.name
            if (self.__sample_path / "src").exists():
                self.__sample_src_path = self.__sample_path / "src"
            elif (self.__sample_path / sample_name).exists():
                self.__sample_src_path = self.__sample_path / sample_name
            else:
                raise ValueError(f"No src directory found in {self.__sample_path}")
        return self.__sample_path

    @property
    def sample_path(self) -> Path:
        if self.__sample_path is None:
            raise ValueError("Sample path not set")
        return self.__sample_path

    @property
    def sample_src_path(self) -> Path:
        if self.__sample_src_path is None:
            raise ValueError("Sample src path not set")
        return self.__sample_src_path

    @property
    def node_id(self) -> str:
        if self.__node_id is None:
            raise ValueError("Node id not set")
        return self.__node_id

    @node_id.setter
    def node_id(self, node_id: str):
        self.__node_id = node_id

    def prefix_from_pytest_localpath(self, path: LocalPath):
        self._path = self._prefix(path) / self._path

    def prepare(self):
        raise NotImplementedError("This method should be implemented by the subclass")

    def cleanup(self):
        raise NotImplementedError("This method should be implemented by the subclass")


class InaccessiblePath(TestPath):
    def __init__(self, path: str):
        super().__init__(path)
        self._original_mode: int | None = None

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["original_mode"] = self._original_mode
        return data

    @override
    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self._original_mode = data["original_mode"]

    @override
    def prepare(self):
        # Remove read permissions (owner/group/others) only for the target file
        path = self._path
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File {path} not found")

        try:
            current_mode = stat.S_IMODE(os.lstat(path).st_mode)
            self._original_mode = current_mode
            new_mode = current_mode & ~(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            try:
                os.chmod(path, new_mode, follow_symlinks=False)
            except (NotImplementedError, TypeError):
                os.chmod(path, new_mode)
        except (FileNotFoundError, PermissionError):
            # Best-effort: if we cannot change it, skip silently for test stability
            return

    @override
    def cleanup(self):
        if not self._original_mode:
            return
        # Restore original permissions if they were changed
        path = self._path
        original_mode = self._original_mode
        if original_mode is None or not path.exists() or not path.is_file():
            return
        try:
            try:
                os.chmod(path, original_mode, follow_symlinks=False)
            except (NotImplementedError, TypeError):
                os.chmod(path, original_mode)
        except (FileNotFoundError, PermissionError):
            return


class SymlinkPath(TestPath):
    def __init__(self, path: str, target: str, relative: bool = True):
        super().__init__(path)
        self._target = Path(target)
        self._relative = relative
        self._created = False

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["target"] = str(self._target)
        data["relative"] = self._relative
        data["created"] = self._created
        return data

    @override
    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self._target = Path(data["target"])
        self._relative = data["relative"]
        self._created = data["created"]

    @override
    def prefix_from_pytest_localpath(self, path: LocalPath):
        super().prefix_from_pytest_localpath(path)
        self._target = self._prefix(path) / self._target

    def prepare(self):
        if SymbolicLink.exists(self._path):
            self._path.unlink()

        if SymbolicLink.exists(self._target):
            self._target.unlink()

        if self._relative:
            self._path = self._path.relative_to(self.sample_src_path)
            self._target = self._target.relative_to(self.sample_src_path)

    @override
    def cleanup(self):
        if not self._created:
            return
        if self._relative:
            self._path = self.sample_src_path / self._path
            self._target = self.sample_src_path / self._target
        try:
            if SymbolicLink.exists(self._path):
                self._path.unlink()
            if SymbolicLink.exists(self._target):
                self._target.unlink()
        finally:
            self._created = False


class BrokenSymlinkPath(SymlinkPath):
    @override
    def prepare(self):
        super().prepare()

        current_cwd = Path.cwd()
        try:
            os.chdir(self.sample_src_path)
            os.symlink(str(self._target), str(self._path))
            self._created = True
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)


class SymlinkSelfLoopPath(SymlinkPath):
    def __init__(self, path: str):
        super().__init__(path, path)

    @override
    def prepare(self):
        super().prepare()

        current_cwd = Path.cwd()
        try:
            os.chdir(self.sample_src_path)
            os.symlink(str(self._target), str(self._path))
            self._created = True
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)


class SymlinkChainCyclePath(SymlinkPath):
    def __init__(self, path: str, length: int):
        super().__init__(path, path)
        # minus one because we only create intermediate links
        # So if we requesting a 2-node cycle, we only create one intermediate link.
        # Since we are using range() to iterate, we need to subtract 1 since upper bound
        # is exclusive.
        self._length = length - 1

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["length"] = self._length
        return data

    @override
    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self._length = data["length"]

    def __link_chain(self) -> Generator[Path, None, None]:
        for index in range(self._length):
            target = Path(f"{self._target.name}-{index}")
            yield target

    @override
    def prepare(self):
        super().prepare()

        current_cwd = Path.cwd()
        try:
            os.chdir(self.sample_src_path)
            source = self._path
            for target in self.__link_chain():
                os.symlink(str(target), str(source))
                source = target
            os.symlink(str(self._target), str(source))
            self._created = True
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)

    @override
    def cleanup(self):
        if not self._created:
            return
        current_cwd = Path.cwd()
        try:
            os.chdir(self.sample_src_path)
            for target in self.__link_chain():
                target.unlink()
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)
        super().cleanup()


class SymlinkTwoNodeCyclePath(SymlinkChainCyclePath):
    def __init__(self, path: str):
        super().__init__(path, 2)


class SymlinkMultiNodeCyclePath(SymlinkChainCyclePath):
    def __init__(self, path: str):
        super().__init__(path, 5)


class SymlinkMaxStepReachedPath(SymlinkChainCyclePath):
    def __init__(self, path: str):
        super().__init__(path, 1000)


class SymlinkEscapingPath(SymlinkPath):
    def __init__(self, path: str, target: str):
        super().__init__(path, target)

    @override
    def prepare(self):
        if not self._target.exists():
            raise FileNotFoundError(f"File {self._target} not found")

        if SymbolicLink.exists(self._path):
            self._path.unlink()

        if self._relative:
            self._path = self._path.relative_to(self.sample_src_path)

        current_cwd = Path.cwd()
        try:
            os.chdir(self.sample_src_path)
            os.symlink(str(self._target), str(self._path))
            self._created = True
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)


class SymlinkPointsToUnreadableFilePath(SymlinkPath):
    def __init__(self, path: str, target: str):
        super().__init__(path, target)
        self._inaccessible_path = InaccessiblePath(target)

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["inaccessible_path"] = self._inaccessible_path.to_json()
        return data

    @override
    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self._inaccessible_path = InaccessiblePath.deserialize(
            data["inaccessible_path"]
        )

    @override
    def prefix_from_pytest_localpath(self, path: LocalPath):
        super().prefix_from_pytest_localpath(path)
        self._inaccessible_path.prefix_from_pytest_localpath(path)

    @override
    @TestPath.node_id.setter
    def node_id(self, node_id: str):
        TestPath.node_id.fset(self, node_id)
        self._inaccessible_path.node_id = node_id

    @override
    def prepare(self):
        if self._relative:
            self._path = self._path.relative_to(self.sample_src_path)
            self._target = self._target.relative_to(self.sample_src_path)

        current_cwd = Path.cwd()
        try:
            os.chdir(self.sample_src_path)
            if SymbolicLink.exists(self._path):
                self._path.unlink()
            if not self._target.exists():
                raise FileNotFoundError(f"File {self._target} not found")
            if not self._target.is_file():
                raise FileNotFoundError(f"File {self._target} is not a file")
            os.symlink(str(self._target), str(self._path))
            self._inaccessible_path.prepare()
            self._created = True
        except (OSError, NotImplementedError) as exc:
            self._inaccessible_path.cleanup()
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)

    @override
    def cleanup(self):
        if not self._created:
            return
        current_cwd = Path.cwd()
        try:
            os.chdir(self.sample_src_path)
            self._inaccessible_path.cleanup()
        finally:
            os.chdir(current_cwd)

        super().cleanup()
