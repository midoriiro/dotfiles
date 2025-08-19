import os
import shutil
import stat
import sys
import tempfile
import uuid
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
        self._sample_path = None
        self._sample_src_path = None
        self.__node_id = None

    def to_json(self) -> Dict[str, Any]:
        if self._sample_path is None:
            raise ValueError("Sample path not set")
        if self._sample_src_path is None:
            raise ValueError("Sample src path not set")
        if self.__node_id is None:
            raise ValueError("Node id not set")
        return {
            "type": self.__class__.__name__,
            "path": str(self._path),
            "sample_path": str(self._sample_path),
            "sample_src_path": str(self._sample_src_path),
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
        self._sample_path = Path(data["sample_path"])
        self._sample_src_path = Path(data["sample_src_path"])
        self.__node_id = data["node_id"]

    def _prefix(self, path: LocalPath) -> Path:
        if self._sample_path is None:
            self._sample_path = _transform_case_path_to_sample_path(
                Path(path.dirname), path.purebasename
            )
            sample_name = self._sample_path.name
            if (self._sample_path / "src").exists():
                self._sample_src_path = self._sample_path / "src"
            elif (self._sample_path / sample_name).exists():
                self._sample_src_path = self._sample_path / sample_name
            else:
                raise ValueError(f"No src directory found in {self._sample_path}")
        return self._sample_path

    @property
    def sample_path(self) -> Path:
        if self._sample_path is None:
            raise ValueError("Sample path not set")
        return self._sample_path

    @property
    def sample_src_path(self) -> Path:
        if self._sample_src_path is None:
            raise ValueError("Sample src path not set")
        return self._sample_src_path

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
    @override
    def prepare(self):
        path = self._path

        if not path.exists() or (not path.is_file() and not path.is_dir()):
            raise FileNotFoundError(f"File {path} not found")

        current_mode = stat.S_IMODE(os.lstat(path).st_mode)
        new_mode = current_mode & ~(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            os.chmod(path, new_mode, follow_symlinks=False)
        except (NotImplementedError, TypeError):
            os.chmod(path, new_mode)

    @override
    def cleanup(self):
        path = self._path

        if not path.exists() or (not path.is_file() and not path.is_dir()):
            raise FileNotFoundError(f"File {path} not found")

        current_mode = stat.S_IMODE(os.lstat(path).st_mode)
        new_mode = current_mode | (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            os.chmod(path, new_mode, follow_symlinks=False)
        except (NotImplementedError, TypeError):
            os.chmod(path, new_mode)


class EmptyDirectoryPath(TestPath):
    def __init__(self, path: str):
        super().__init__(path)
        self.__created = False

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["created"] = self.__created
        return data

    @override
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self.__created = data["created"]

    @override
    def _prefix(self, path: LocalPath):
        if self._sample_path is None:
            self._sample_path = _transform_case_path_to_sample_path(
                Path(path.dirname), path.purebasename
            )
            self._sample_src_path = self._sample_path / "src"
        return self._sample_path

    @override
    def prepare(self):
        if self._path.exists():
            shutil.rmtree(self._path, ignore_errors=True)
        self._path.mkdir(parents=True, exist_ok=True)
        self.__created = True

    @override
    def cleanup(self):
        if not self.__created:
            return
        shutil.rmtree(self._path, ignore_errors=True)


class SymlinkPath(TestPath):
    def __init__(
        self,
        path: str,
        target: str,
        relative: bool = True,
        should_exists: bool = False,
    ):
        super().__init__(path)
        self._target = Path(target)
        self._relative = relative
        self._base_path = None
        self._should_exists = should_exists
        self._created = False

    @override
    def _prefix(self, path: LocalPath):
        path = super()._prefix(path)
        if self._relative and self._should_exists:
            if (self.sample_src_path / self._target).exists():
                self._base_path = self.sample_src_path
            elif (self.sample_path / self._target).exists():
                self._base_path = self.sample_path
            else:
                raise ValueError(
                    "Provided target should be relative to project root directory or "
                    "source directory"
                )
        else:
            self._base_path = self.sample_src_path
        return path

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["target"] = str(self._target)
        data["relative"] = self._relative
        data["base_path"] = str(self._base_path)
        data["should_exists"] = self._should_exists
        data["created"] = self._created
        return data

    @override
    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self._target = Path(data["target"])
        self._relative = data["relative"]
        self._base_path = Path(data["base_path"])
        self._should_exists = data["should_exists"]
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
            self._path = self._path.relative_to(self._base_path)
            self._target = self._target.relative_to(self._base_path)

    @override
    def cleanup(self):
        if not self._created:
            return
        if self._relative:
            self._path = self._base_path / self._path
            self._target = self._base_path / self._target
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
            os.chdir(self._base_path)
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
            os.chdir(self._base_path)
            os.symlink(str(self._target), str(self._path))
            self._created = True
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)


class SymlinkChainCyclePath(SymlinkPath):
    def __init__(self, path: str, target: str, length: int):
        super().__init__(path, target)
        # minus one because we only create intermediate links
        # So if we requesting a 2-node cycle, we only create one intermediate link.
        # Since we are using range() to iterate, we need to subtract 1 since upper bound
        # is exclusive.
        if length < 2:
            raise ValueError("Length must be at least 2")
        self.__length = length - 1

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["length"] = self.__length
        return data

    @override
    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self.__length = data["length"]

    def __link_chain(self) -> Generator[Path, None, None]:
        for index in range(self.__length):
            target = Path(f"{self._target.name}-{index}")
            yield target

    @override
    def prepare(self):
        super().prepare()

        current_cwd = Path.cwd()
        try:
            os.chdir(self._base_path)

            for target in self.__link_chain():
                if SymbolicLink.exists(target):
                    target.unlink()

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
            os.chdir(self._base_path)
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
        super().__init__(path, path, 2)


class SymlinkMultiNodeCyclePath(SymlinkChainCyclePath):
    def __init__(self, path: str):
        super().__init__(path, path, 5)


class SymlinkMultiNodeHopPath(SymlinkChainCyclePath):
    def __init__(self, path: str, target: str):
        super().__init__(path, target, 5)


class SymlinkMaxStepReachedPath(SymlinkChainCyclePath):
    def __init__(self, path: str):
        super().__init__(path, path, 1000)


class SymlinkEscapePath(SymlinkPath):
    def __init__(self, path: str, target: str):
        super().__init__(path, target)

    @override
    def prepare(self):
        if not self._target.exists():
            raise FileNotFoundError(f"File {self._target} not found")

        if SymbolicLink.exists(self._path):
            self._path.unlink()

        if self._relative:
            self._path = self._path.relative_to(self._base_path)

        current_cwd = Path.cwd()
        try:
            os.chdir(self._base_path)
            os.symlink(str(self._target), str(self._path))
            self._created = True
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)


class SymlinkEscapeMidwayPath(SymlinkPath):
    def __init__(self, path: str, target: str):
        super().__init__(path, target)
        self.__length = 4
        self.__length_mid = 2
        self.__temp_dirname_id = uuid.uuid4().hex[:8]

    @override
    def to_json(self) -> dict[str, Any]:
        data = super().to_json()
        data["length"] = self.__length
        data["length_mid"] = self.__length_mid
        data["temp_dirname_id"] = self.__temp_dirname_id
        return data

    @override
    # pylint: disable=protected-access,unused-private-member
    def from_json(self, data: Dict[str, Any]):
        super().from_json(data)
        self.__length = data["length"]
        self.__length_mid = data["length_mid"]
        self.__temp_dirname_id = data["temp_dirname_id"]

    def __link_chain(self) -> Generator[Path, None, None]:
        length = self.__length + 1
        for index in range(length):
            target = Path(f"{self._path.name}-{index}")
            yield target

    def __midway_symlink_path(self) -> Path:
        temp_dir = tempfile.gettempdir()
        path = Path(temp_dir) / f"{self.__temp_dirname_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path / "midway-symlink"

    @override
    def prepare(self):
        super().prepare()

        current_cwd = Path.cwd()
        midway_symlink_path = self.__midway_symlink_path()
        try:
            os.chdir(self._base_path)

            for target in self.__link_chain():
                if SymbolicLink.exists(target):
                    target.unlink()

            source = self._path
            chain = self.__link_chain()

            for _ in range(self.__length_mid):
                target = next(chain)
                os.symlink(str(target), str(source))
                source = target

            target = midway_symlink_path
            os.symlink(str(target), str(source))
            source = target

            target = next(chain)
            os.symlink(str(target.absolute()), str(source))
            source = target

            for _ in range(self.__length_mid):
                target = next(chain)
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
            if SymbolicLink.exists(self._path):
                self._path.unlink()
            if SymbolicLink.exists(self._target):
                self._target.unlink()
            os.chdir(self._base_path)
            for target in self.__link_chain():
                target.unlink()
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)
            midway_symlink_path = self.__midway_symlink_path()
            if midway_symlink_path.parent.exists():
                midway_symlink_path.unlink()
                midway_symlink_path.parent.rmdir()
        super().cleanup()


class SymlinkPointToUnreadablePath(SymlinkPath):
    def __init__(self, path: str, target: str):
        super().__init__(path, target, should_exists=True)
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
        super().prepare()

        current_cwd = Path.cwd()
        try:
            os.chdir(self._base_path)

            if SymbolicLink.exists(self._path):
                self._path.unlink()

            if not self._target.exists():
                raise FileNotFoundError(f"File {self._target} not found")

            if not self._target.is_file() and not self._target.is_dir():
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
            os.chdir(self._base_path)
            self._inaccessible_path.cleanup()
        finally:
            os.chdir(current_cwd)

        super().cleanup()


class SymlinkPointToAbsolutePath(SymlinkPath):
    def __init__(self, path: str, target: str):
        super().__init__(path, target, relative=False)

    @override
    def prepare(self):
        super().prepare()

        current_cwd = Path.cwd()
        try:
            os.chdir(self._base_path)
            os.symlink(str(self._target), str(self._path))
            self._created = True
        except (OSError, NotImplementedError) as exc:
            # On some Windows setups, symlink creation may be restricted
            msg = f"Symlink creation not supported on this platform: {exc}"
            raise RuntimeError(msg) from exc
        finally:
            os.chdir(current_cwd)
