import os
import stat
from pathlib import Path
from typing import List, Optional


class SymlinkError(Exception):
    pass


class NotSymlinkError(SymlinkError):
    def __init__(self, path: Path):
        super().__init__(f"Not a symbolic link: {path}")


class BrokenSymlinkError(SymlinkError):
    def __init__(self, path: Path, target: Path):
        super().__init__(f"Broken symbolic link: {path} -> {target}")


class SymlinkNotAccessibleError(SymlinkError):
    def __init__(self, path: Path, target: Path):
        super().__init__(
            f"Symbolic link target '{path}' -> '{target}' cannot be read: "
            "insufficient permissions or file does not exist"
        )


class SymlinkCyclicalError(SymlinkError):
    def __init__(self, path: Path, chain: List[Path], note: Optional[str] = None):
        self.path = path
        self.chain = " -> ".join([str(p) for p in chain])
        self.note = note
        msg = f"Symbolic link is cyclical: {self.path} -> {self.chain}"
        if note:
            msg += f" ({note})"
        super().__init__(msg)

    @property
    def cycle_length(self) -> int:
        return len(self.chain)


class SymlinkSelfLoopError(SymlinkCyclicalError):
    """Length-1 cycle: a -> a."""

    def __init__(self, path: Path, chain: List[Path]):
        super().__init__(path, chain, note="self-loop (length=1)")


class SymlinkTwoNodeCycleError(SymlinkCyclicalError):
    """Length-2 cycle: a -> b -> a."""

    def __init__(self, path: Path, chain: List[Path]):
        super().__init__(path, chain, note="2-node cycle (length=2)")


class SymlinkChainCycleError(SymlinkCyclicalError):
    """Multi-node cycle: a -> b -> ... -> a."""

    def __init__(self, path: Path, chain: List[Path]):
        super().__init__(path, chain, note=f"multi-node cycle (length={len(chain)})")


class SymlinkMaxStepReachedError(SymlinkError):
    def __init__(self, path: Path, chain: List[Path]):
        super().__init__(
            f"Symbolic link '{path}' cannot be resolved and has reached maximum steps "
            f"allowed ({len(chain)}) during cycle detection phase. For security "
            "reasons, this is not allowed."
        )


class SymlinkEscapingError(SymlinkError):
    def __init__(self, path: Path, target: Path, base_path: Path):
        super().__init__(
            f"Symbolic link target '{path}' -> '{target}' escaped base path: "
            f"{base_path}"
        )


def _raise_cycle_error(path: Path, chain: List[Path]):
    if not chain:
        raise SymlinkCyclicalError(path, chain, note="empty chain (?)")

    if len(chain) == 1 or (len(chain) == 2 and chain[0] == chain[-1]):
        raise SymlinkSelfLoopError(path, chain)

    unique_nodes = set(chain)
    if len(unique_nodes) == 2:
        raise SymlinkTwoNodeCycleError(path, chain)

    raise SymlinkChainCycleError(path, chain)


class __ResolveResult:  # pylint: disable=invalid-name
    def __init__(self, is_cyclic: bool, max_step_reached: bool, chain: List[Path]):
        self.is_cyclic = is_cyclic
        self.max_step_reached = max_step_reached
        self.chain = chain


def _resolve(start: Path, max_steps: int = 1000) -> __ResolveResult:
    _ensure_symlink(start)
    seen = set()
    chain = []
    p = start

    for _ in range(max_steps):
        chain.append(p)

        try:
            st = os.lstat(p)
        except (FileNotFoundError, PermissionError):
            return __ResolveResult(is_cyclic=False, max_step_reached=False, chain=chain)

        if not stat.S_ISLNK(st.st_mode):
            return __ResolveResult(is_cyclic=False, max_step_reached=False, chain=chain)

        key = (st.st_dev, st.st_ino)
        if key in seen:
            return __ResolveResult(is_cyclic=True, max_step_reached=False, chain=chain)
        seen.add(key)

        p = _resolve_one_hop(p)

    return __ResolveResult(is_cyclic=True, max_step_reached=True, chain=chain)


def _resolve_one_hop(path: Path) -> Path:
    _ensure_symlink(path)
    target = Path(os.readlink(path))
    if not target.is_absolute():
        target = path.parent / target
    return Path(os.path.normpath(str(target)))


def _resolve_all_hops(path: Path) -> Path:
    _ensure_symlink(path)
    result = _resolve(path, max_steps=1000)
    if not result.is_cyclic:
        return result.chain[-1]
    if result.max_step_reached:
        raise SymlinkMaxStepReachedError(path, result.chain)
    _raise_cycle_error(path, result.chain)


def _ensure_symlink(path: Path):
    if not path.is_symlink():
        raise NotSymlinkError(path)


class SymbolicLink:
    def __init__(self, path: Path):
        _ensure_symlink(path)
        self.__path = path
        self.__target = _resolve_all_hops(path)

    @property
    def path(self) -> Path:
        return self.__path

    @property
    def target(self) -> Path:
        return self.__target

    @staticmethod
    def exists(path: Path) -> bool:
        try:
            _ensure_symlink(path)
            os.lstat(path)
            return True
        except (NotSymlinkError, FileNotFoundError):
            return False

    def is_broken(self):
        if self.__target.exists():
            return
        raise BrokenSymlinkError(self.__path, self.__target)

    def is_escaping(self, base_path: Path):
        if self.__target.is_relative_to(base_path):
            return
        raise SymlinkEscapingError(self.__path, self.__target, base_path)

    def is_accessible(self):
        if (
            self.__target.is_file() or self.__target.is_dir()
        ) and self.__target.stat().st_mode & 0o444:
            return
        raise SymlinkNotAccessibleError(self.__path, self.__target)
