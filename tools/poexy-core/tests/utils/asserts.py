import difflib
from enum import Flag, auto
from pathlib import Path
from typing import Iterable, List, Optional, Union

from assertpy import assert_that

from poexy_core.utils.enums import ExtendedEnum


def assert_collections_equal(expected: Iterable[Path], actual: Iterable[Path]):
    sorted_expected = sorted(expected)
    sorted_actual = sorted(actual)
    try:
        assert_that(len(sorted_expected)).is_equal_to(len(sorted_actual))
        assert_that(sorted_expected).is_equal_to(sorted_actual)
    except AssertionError as exc:
        diff = difflib.unified_diff(
            [f"'{x}'\n" for x in sorted_expected],
            [f"'{x}'\n" for x in sorted_actual],
            fromfile="expected",
            tofile="actual",
        )
        raise AssertionError("Lists differ:\n" + "".join(diff)) from exc


class MarkBuffer:
    def __init__(self, path: Path):
        self.parts = list(path.parts)

    @property
    def path(self) -> Path:
        return Path(*self.parts)

    def __str__(self):
        return f"{self.path}"


class MarkParserError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class MarkParser:
    def usage(self) -> str:
        raise NotImplementedError("Subclass must implement this method")

    def parse(self, buffer: MarkBuffer):
        raise NotImplementedError("Subclass must implement this method")


class ExcludeMarkParser(MarkParser):
    def __init__(self):
        self.__have_exclude_mark = False

    @property
    def have_exclude_mark(self):
        return self.__have_exclude_mark

    def usage(self) -> str:
        return "[!:]"

    def parse(self, buffer: MarkBuffer):
        for index, part in enumerate(buffer.parts):
            if part.startswith("!:") and index != 0:
                raise MarkParserError(
                    "Exclude mark must be located at the beginning of the path: "
                    f"{buffer}"
                )

            if not part.startswith("!:"):
                continue

            cleaned_part = part.split(":", maxsplit=1)[1]
            buffer.parts[index] = cleaned_part
            self.__have_exclude_mark = True
            return


class TargetMarkParser(MarkParser):
    def __init__(self):
        self.__all_target_mark_values = [
            AssertPathMarker.Tar.value,
            AssertPathMarker.Wheel.value,
            AssertPathMarker.All.value,
        ]
        self.__target_mark: Optional[AssertPathPackageTarget] = None

    @property
    def target_mark(self):
        if self.__target_mark is None:
            raise MarkParserError("Target mark is not set")
        return self.__target_mark

    def usage(self) -> str:
        return f"[ [{' | '.join(self.__all_target_mark_values)}] : ]"

    def __any_startswith(self, part: str):
        return any(
            part.startswith(f"{mark}:") for mark in self.__all_target_mark_values
        )

    def parse(self, buffer: MarkBuffer):
        for index, part in enumerate(buffer.parts):
            if self.__any_startswith(part) and index != 0:
                raise MarkParserError(
                    "Target mark must be located at the beginning of the path: "
                    f"{buffer}"
                )

            if not self.__any_startswith(part):
                continue

            if part.startswith(f"{AssertPathMarker.Tar.value}:"):
                target = AssertPathPackageTarget.Tar
            elif part.startswith(f"{AssertPathMarker.Wheel.value}:"):
                target = AssertPathPackageTarget.Wheel
            elif part.startswith(f"{AssertPathMarker.All.value}:"):
                target = AssertPathPackageTarget.All
            else:
                raise MarkParserError(
                    f"Invalid target mark: {part}. Valid target marks are: "
                    f"{', '.join(self.__all_target_mark_values)}"
                )

            cleaned_part = part.split(":", maxsplit=1)[1]
            buffer.parts[index] = cleaned_part

            self.__target_mark = target
            return

        self.__target_mark = AssertPathPackageTarget.All


class KindMarkParser(MarkParser):
    def __init__(self):
        self.__all_kind_mark_values = [
            AssertPathMarker.File.value,
            AssertPathMarker.Link.value,
            AssertPathMarker.Platform.value,
            AssertPathMarker.Data.value,
            AssertPathMarker.Config.value,
            AssertPathMarker.Cache.value,
            AssertPathMarker.Purelib.value,
            AssertPathMarker.Platlib.value,
            AssertPathMarker.Binary.value,
        ]
        self.__kind_mark: Optional[AssertPathKind] = None

    @property
    def kind_mark(self) -> "AssertPathKind":
        if self.__kind_mark is None:
            raise MarkParserError("Kind mark is not set")
        return self.__kind_mark

    def __any_endswith(self, part: str):
        return any(part.endswith(f":{mark}") for mark in self.__all_kind_mark_values)

    def usage(self) -> str:
        return f"[ [{' | '.join(self.__all_kind_mark_values)}] : ]"

    def parse(self, buffer: MarkBuffer):
        last_index = len(buffer.parts) - 1
        for index, part in enumerate(buffer.parts):
            if self.__any_endswith(part) and index < last_index:
                raise MarkParserError(
                    f"Kind marks must be located at the end of the path: {buffer}"
                )

            if not self.__any_endswith(part):
                continue

            name_and_markers = part.split(":")
            name = name_and_markers[0]

            markers = []

            for marker in name_and_markers[1:]:
                if marker not in AssertPathMarker:
                    raise MarkParserError(f"Invalid marker: {marker}")
                markers.append(AssertPathMarker(marker))

            kind = AssertPathKind.Default | AssertPathKind.Purelib

            for marker in markers:
                if marker not in AssertPathMarker:
                    raise MarkParserError(f"Invalid marker: {marker}")
                if marker == AssertPathMarker.File:
                    kind |= AssertPathKind.File
                elif marker == AssertPathMarker.Link:
                    kind |= AssertPathKind.Link
                elif marker == AssertPathMarker.Platform:
                    kind |= AssertPathKind.Platform
                    kind &= ~AssertPathKind.Purelib
                elif marker == AssertPathMarker.Data:
                    kind |= AssertPathKind.Data
                elif marker == AssertPathMarker.Config:
                    kind |= AssertPathKind.Config
                elif marker == AssertPathMarker.Cache:
                    kind |= AssertPathKind.Cache
                elif marker == AssertPathMarker.Purelib:
                    kind |= AssertPathKind.Purelib
                elif marker == AssertPathMarker.Platlib:
                    kind |= AssertPathKind.Platlib
                    kind &= ~AssertPathKind.Purelib
                elif marker == AssertPathMarker.Binary:
                    kind |= AssertPathKind.Binary
                    kind &= ~AssertPathKind.Purelib

            kind &= ~AssertPathKind.Default

            buffer.parts[index] = name
            self.__kind_mark = kind
            return

        self.__kind_mark = AssertPathKind.Default | AssertPathKind.Purelib


class MarkParserFactory:
    def __init__(self):
        self.__exclude_mark_parser = ExcludeMarkParser()
        self.__target_mark_parser = TargetMarkParser()
        self.__kind_mark_parser = KindMarkParser()

    def __usage(self) -> str:
        exclude_usage = self.__exclude_mark_parser.usage()
        target_usage = self.__target_mark_parser.usage()
        kind_usage = self.__kind_mark_parser.usage()

        return f"{exclude_usage} {target_usage} PATH {kind_usage}"

    def parse(self, path: Path) -> "AssertPath":
        buffer = MarkBuffer(path)

        try:
            self.__exclude_mark_parser.parse(buffer)
            self.__target_mark_parser.parse(buffer)
            self.__kind_mark_parser.parse(buffer)
        except MarkParserError as exc:
            raise MarkParserError(
                f"Error parsing path: {path}: {exc}\n\n" f"Usage: {self.__usage()}"
            ) from exc

        is_excluded = self.__exclude_mark_parser.have_exclude_mark
        target = self.__target_mark_parser.target_mark
        kind = self.__kind_mark_parser.kind_mark

        return AssertPath(buffer.path, kind, target, is_excluded)


AssertPathType = Union[str, Path]


class AssertPathKind(Flag):
    Default = 1

    # File types
    File = auto()
    Link = auto()

    # Platform types
    Platform = auto()
    Data = auto()
    Config = auto()
    Cache = auto()

    # Destinations
    Purelib = auto()
    Platlib = auto()
    Binary = auto()


class AssertPathPackageTarget(Flag):
    Tar = 1
    Wheel = auto()
    All = Tar | Wheel


class AssertPathMarker(str, ExtendedEnum):
    # File types
    File = "file"
    Link = "ln"

    # Platform types
    Platform = "plat"
    Data = "data"
    Config = "cfg"
    Cache = "cache"

    # Destinations
    Purelib = "purelib"
    Platlib = "platlib"
    Binary = "bin"

    # Package types
    Tar = "tar"
    Wheel = "whl"
    All = "all"


class AssertPath:
    def __init__(
        self,
        path: Path,
        kind: AssertPathKind,
        target: AssertPathPackageTarget,
        is_excluded: bool,
    ):
        self.path = path
        self.kind = kind
        self.target = target
        self.is_excluded = is_excluded

    def __eq__(self, other: Union["AssertPath", Path, str]):
        if isinstance(other, AssertPath):
            return self.path == other.path
        if isinstance(other, str):
            return str(self.path) == other
        if isinstance(other, Path):
            return str(self.path) == str(other)
        raise ValueError(f"Cannot compare AssertPath with {type(other)}")

    def __ne__(self, value: "AssertPath") -> bool:
        return not self == value

    def __lt__(self, other: "AssertPath") -> bool:
        if self.path.parent != other.path.parent:
            return str(self.path) < str(other.path)
        return self.path.name < other.path.name

    def __le__(self, other: "AssertPath") -> bool:
        return self < other or self == other

    def __gt__(self, other: "AssertPath") -> bool:
        return not self <= other

    def __ge__(self, other: "AssertPath") -> bool:
        return not self < other

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return (
            f"AssertPath({self.path}, {self.kind}, {self.target}, {self.is_excluded})"
        )

    def __hash__(self):
        return hash(self.path)

    def expand(self, value: str):
        if AssertPathKind.Binary in self.kind:
            variable_name = "$BINARY"
        else:
            raise ValueError(f"Cannot expand type {self.kind}")

        parts = list(self.path.parts)
        for index, part in enumerate(parts):
            if part == variable_name:
                parts[index] = value
                self.path = Path(*parts)
                return

        raise ValueError(f"Variable {variable_name} not found in {self.path}")

    @staticmethod
    def from_base_path(path: AssertPathType, base_path: Path) -> "AssertPath":
        if isinstance(path, str):
            path = Path(path)
        assert_path = AssertPath.parse(path)
        assert_path.path = base_path / assert_path.path
        return assert_path

    @staticmethod
    def parse(path: AssertPathType) -> "AssertPath":
        if isinstance(path, str):
            path = Path(path)

        parser = MarkParserFactory()
        return parser.parse(path)


class AssertPaths:
    def __init__(self, paths: List[Union[AssertPathType, "AssertPath"]]):
        if not any(not isinstance(path, AssertPath) for path in paths):
            self.__all: List[AssertPath] = paths
        else:
            self.__all: List[AssertPath] = [AssertPath.parse(path) for path in paths]

        self.__included = [path for path in self.__all if not path.is_excluded]
        self.__excluded = [path for path in self.__all if path.is_excluded]

        self.__files = [
            path for path in self.__included if AssertPathKind.File in path.kind
        ]
        self.__links = [
            path for path in self.__included if AssertPathKind.Link in path.kind
        ]
        self.__platforms = [
            path for path in self.__included if AssertPathKind.Platform in path.kind
        ]
        self.__binaries = [
            path for path in self.__included if AssertPathKind.Binary in path.kind
        ]

    def __len__(self):
        return len(self.__all)

    def __iter__(self):
        return iter(self.all)

    def all(self):
        return [assert_path.path for assert_path in self.__all]

    @staticmethod
    def __reduce_from_target(paths: List[AssertPath], target: AssertPathPackageTarget):
        return [
            assert_path.path for assert_path in paths if target in assert_path.target
        ]

    def included(self, target: AssertPathPackageTarget = AssertPathPackageTarget.All):
        return self.__reduce_from_target(self.__included, target)

    def excluded(self, target: AssertPathPackageTarget = AssertPathPackageTarget.All):
        return self.__reduce_from_target(self.__excluded, target)

    def files(self, target: AssertPathPackageTarget = AssertPathPackageTarget.All):
        return self.__reduce_from_target(self.__files, target)

    def links(self, target: AssertPathPackageTarget = AssertPathPackageTarget.All):
        return self.__reduce_from_target(self.__links, target)

    def platforms(self, target: AssertPathPackageTarget = AssertPathPackageTarget.All):
        return self.__reduce_from_target(self.__platforms, target)

    def binaries(self, target: AssertPathPackageTarget = AssertPathPackageTarget.All):
        return self.__reduce_from_target(self.__binaries, target)

    def remap_base_path(
        self, base_path: Path, path_kind: Optional[AssertPathKind] = None
    ):
        if path_kind is None:
            for assert_path in self.__all:
                assert_path.path = base_path / assert_path.path
        else:
            for assert_path in self.__all:
                if (
                    AssertPathKind.Default in path_kind
                    and assert_path.kind == AssertPathKind.Default
                ):
                    assert_path.path = base_path / assert_path.path
                    continue
                if path_kind in assert_path.kind:
                    assert_path.path = base_path / assert_path.path

    def expand(self, value: str, path_kind: AssertPathKind):
        for assert_path in self.__all:
            if path_kind in assert_path.kind:
                assert_path.expand(value)

    @staticmethod
    def from_base_path(paths: List[AssertPathType], base_path: Path) -> "AssertPaths":
        return AssertPaths(
            [AssertPath.from_base_path(path, base_path) for path in paths]
        )


AssertPathsType = Union[List[AssertPathType], AssertPaths]
