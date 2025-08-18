from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, override

from poexy_core.utils.symbolic_link import SymbolicLink

from .exceptions import InaccessiblePathError

if TYPE_CHECKING:
    from ..models import PackageFile

# pylint: disable=no-member,import-outside-toplevel


class ResolverSymlinkPolicy(ABC):
    @abstractmethod
    def validate(self, symlink: SymbolicLink, base_path: Path):
        raise NotImplementedError("Subclass must implement this method")


class DefaultSymlinkPolicy(ResolverSymlinkPolicy):
    @override
    def validate(self, symlink: SymbolicLink, base_path: Path):
        symlink.is_broken()
        symlink.is_escaping(base_path)
        symlink.is_relative()


class ResolverAccesser(ABC):
    @abstractmethod
    def is_accessible(self, base_path: Path, source_path: Path):
        raise NotImplementedError("Subclass must implement this method")


class DefaultRegularFileAccesser(ResolverAccesser):
    @override
    def is_accessible(self, base_path: Path, source_path: Path):
        if source_path.is_file() and source_path.stat().st_mode & 0o444:
            return
        raise InaccessiblePathError(source_path)


class DefaultSymlinkAccesser(ResolverAccesser):
    def __init__(self, symlink_policy: ResolverSymlinkPolicy):
        self._symlink_policy = symlink_policy

    @override
    def is_accessible(self, base_path: Path, source_path: Path):
        symlink = SymbolicLink(source_path, base_path)
        self._symlink_policy.validate(symlink, base_path)
        symlink.is_accessible()


class ResolverNormalizer(ABC):
    def __init__(
        self,
        accesser: ResolverAccesser,
    ):
        self._accesser = accesser

    @abstractmethod
    def normalize(self, base_path: Path, source_path: Path) -> "PackageFile":
        raise NotImplementedError("Subclass must implement this method")


class DefaultRegularFileNormalizer(ResolverNormalizer):
    @override
    def normalize(
        self,
        base_path: Path,
        source_path: Path,
    ) -> "PackageFile":
        from ..models import PackageFile

        self._accesser.is_accessible(base_path, source_path)
        normalized_path = source_path.absolute().relative_to(base_path)
        return PackageFile(
            source=normalized_path,
            destination=normalized_path,
        )


class DefaultSymlinkNormalizer(ResolverNormalizer):
    def __init__(
        self,
        accesser: ResolverAccesser,
        symlink_policy: ResolverSymlinkPolicy,
    ):
        super().__init__(accesser)
        self._symlink_policy = symlink_policy

    @override
    def normalize(
        self,
        base_path: Path,
        source_path: Path,
    ) -> "PackageFile":
        from ..models import SymlinkPackageFile

        symlink = SymbolicLink(source_path, base_path)
        self._symlink_policy.validate(symlink, base_path)
        try:
            self._accesser.is_accessible(base_path, symlink.target)
        except InaccessiblePathError:
            symlink.is_accessible()

        target = symlink.target.relative_to(base_path)

        normalized_path = source_path.absolute().relative_to(base_path)
        return SymlinkPackageFile(
            source=normalized_path,
            destination=normalized_path,
            target=target,
        )


class PackageFileResolverOptions:

    def __init__(
        self,
        accesser: Optional[ResolverAccesser] = None,
        normalizer: Optional[ResolverNormalizer] = None,
        symlink_policy: Optional[ResolverSymlinkPolicy] = None,
        symlink_accesser: Optional[ResolverAccesser] = None,
        symlink_normalizer: Optional[ResolverNormalizer] = None,
        recursive: Optional[bool] = None,
    ):
        self.accesser = accesser
        self.normalizer = normalizer
        self.symlink_policy = symlink_policy
        self.symlink_accesser = symlink_accesser
        self.symlink_normalizer = symlink_normalizer
        self.recursive = recursive

    def get(self) -> Dict[str, Any]:
        values = {}
        if self.accesser is not None:
            values["accesser"] = self.accesser
        if self.normalizer is not None:
            values["normalizer"] = self.normalizer
        if self.symlink_policy is not None:
            values["symlink_policy"] = self.symlink_policy
        if self.symlink_accesser is not None:
            values["symlink_accesser"] = self.symlink_accesser
        if self.symlink_normalizer is not None:
            values["symlink_normalizer"] = self.symlink_normalizer
        if self.recursive is not None:
            values["recursive"] = self.recursive
        return values
