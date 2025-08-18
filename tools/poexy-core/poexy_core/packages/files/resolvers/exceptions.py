from pathlib import Path


class ResolverError(Exception):
    pass


class NoFilesResolvedError(ResolverError):
    pass


class PatternResolvedNothingError(NoFilesResolvedError):
    pattern: str

    def __init__(self, pattern: str):
        self.pattern = pattern
        super().__init__(f"Pattern '{pattern}' resolved nothing")


class DirectoryResolvedNothingError(NoFilesResolvedError):
    def __init__(self, directory: str):
        super().__init__(f"Directory '{directory}' resolved nothing")


class SymlinkResolvedNothingError(NoFilesResolvedError):
    def __init__(self, symlink: str):
        super().__init__(f"Symlink '{symlink}' resolved nothing")


class ResolverValidationError(ResolverError):
    def __init__(self, resolver: str, message: str):
        super().__init__(f"Resolver '{resolver}' validation error: {message}")


class FormatNotAllowedError(ResolverError):
    def __init__(self, resolver: str, format: str):
        super().__init__(f"Format '{format}' is not allowed for resolver '{resolver}'")


class InaccessiblePathError(ResolverError):
    def __init__(self, path: Path):
        super().__init__(
            f"File '{path}' cannot be read: insufficient permissions "
            "or file does not exist"
        )
