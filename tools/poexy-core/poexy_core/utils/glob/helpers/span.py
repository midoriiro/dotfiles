from poexy_core.utils.glob.exceptions import GlobSyntaxError


class Span:
    def __init__(self, start: int, end: int) -> None:
        if start < 0 or end < 0:
            raise GlobSyntaxError("Span start/end must be positive")
        if start > end:
            raise GlobSyntaxError("Span start must be less than end")
        self.start = start
        self.end = end

    @property
    def length(self) -> int:
        return self.end - self.start

    def __str__(self) -> str:
        return f"{self.start}:{self.end}"
