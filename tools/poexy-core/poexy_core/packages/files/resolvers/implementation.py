import os
from pathlib import Path
from typing import TYPE_CHECKING, override

from poexy_core.utils.constants import FORBIDDEN_DIRS
from poexy_core.utils.symbolic_link import SymbolicLink

from .exceptions import PatternResolvedNothingError
from .models import GlobPatternResolver

if TYPE_CHECKING:
    from ..collections import Files


# pylint: disable=no-member,import-outside-toplevel


class DefaultGlobPatternResolver(GlobPatternResolver):
    @override
    def resolve(self) -> "Files":
        from ..collections import Files
        from ..models import SymlinkPackageFile

        glob_pattern = self.glob_pattern
        source_path = Path(os.path.abspath(os.path.normpath(self.path)))

        base_path = Path.cwd()
        source_path = source_path.relative_to(base_path)

        files = Files(list())

        if glob_pattern is None and source_path.is_symlink():
            symlink_file: SymlinkPackageFile = self.symlink_normalizer.normalize(
                base_path=base_path, source_path=source_path
            )
            files.append(symlink_file)
            return files

        if glob_pattern is not None and source_path.is_symlink():
            self.symlink_policy.validate(
                SymbolicLink(source_path, base_path), base_path
            )

        if glob_pattern is None and source_path.is_file():
            file = self.normalizer.normalize(
                base_path=base_path,
                source_path=source_path,
            )
            files.append(file)
            return files

        if glob_pattern is not None:
            str_glob_pattern = str(glob_pattern)
            str_glob_pattern = f"{source_path}/{str_glob_pattern}"
        else:
            str_glob_pattern = str(source_path)

        if self.recursive:
            glob_function = base_path.rglob
        else:
            glob_function = base_path.glob

        for file_source_path in glob_function(str_glob_pattern):
            if not file_source_path.is_file() and not file_source_path.is_symlink():
                continue

            if any(part in FORBIDDEN_DIRS for part in file_source_path.parts):
                continue

            if file_source_path.is_symlink():
                symlink_file: SymlinkPackageFile = self.symlink_normalizer.normalize(
                    base_path=base_path, source_path=file_source_path
                )

                files.append(symlink_file)

                if symlink_file.target.is_file():
                    file = self.normalizer.normalize(
                        base_path=base_path,
                        source_path=symlink_file.target,
                    )
                    files.append(file)
            else:
                file = self.normalizer.normalize(
                    base_path=base_path,
                    source_path=file_source_path,
                )
                files.append(file)

        if len(files) == 0:
            raise PatternResolvedNothingError(pattern=str_glob_pattern)

        return files
