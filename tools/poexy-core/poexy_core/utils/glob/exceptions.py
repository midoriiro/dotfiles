class GlobError(Exception):
    pass


class GlobSyntaxError(GlobError):
    pass


class EndOfInputError(GlobError):
    pass
