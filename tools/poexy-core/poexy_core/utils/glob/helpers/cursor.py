from abc import ABC
from typing import Self

from poexy_core.utils.glob.exceptions import EndOfInputError, GlobSyntaxError
from poexy_core.utils.glob.helpers.input import Input
from poexy_core.utils.glob.helpers.slice import SliceView
from poexy_core.utils.glob.helpers.span import Span


class CursorResult(ABC):
    def __init__(self, span: Span):
        self.span = span


class CursorWithOutputResult(CursorResult):
    def __init__(self, output: SliceView, span: Span):
        super().__init__(span)
        self.output = output


class CursorEmptyResult(CursorResult):
    pass


class Cursor:
    def __init__(self, _input: Input) -> None:
        self._input = _input
        self._length = len(_input)
        self._index = 0

    def as_weak(self) -> Self:
        return WeakCursor(self)

    def at_end(self) -> bool:
        return self._index >= self._length

    def position(self) -> int:
        return self._index

    def seek(self, index: int) -> None:
        if index < 0 or index > self._length:
            raise GlobSyntaxError("Index out of bounds")
        self._index = index

    def advance(self, count: int = 1) -> None:
        self.seek(self._index + count)

    def rewind(self, count: int = 1) -> None:
        self.seek(self._index - count)

    def peek(self, count: int = 1) -> CursorWithOutputResult:
        span = self.__span(self._index, self._index + count)
        output = self._input.get(span.start, span.end)
        return CursorWithOutputResult(output=output, span=span)

    def consume(self, count: int = 1) -> CursorWithOutputResult:
        result = self.peek(count)
        self._index += count
        return result

    def expect(self, _input: str) -> CursorEmptyResult:
        span = self.__span(self._index, self._index + len(_input))

        if not self._input.startswith(_input, span.start):
            raise GlobSyntaxError(self.__error(f"Expected to match '{_input}'"))

        self._index += span.length

        return CursorEmptyResult(span)

    def until(self, _input: str) -> CursorWithOutputResult:
        span = self.__span(self._index, self._index + len(_input))

        count = 0

        while not self.at_end():
            self.consume()
            count += 1
            peek = self.peek(span.length).output

            if peek != _input:
                continue

            self.rewind(count)

            start = self._index
            end = self._index + count
            output = self._input.get(start, end)

            self.seek(end)

            return CursorWithOutputResult(output=output, span=Span(start, end))

        raise GlobSyntaxError(self.__error(f"Expected to match '{_input}'"))

    def __span(self, start: int, end: int) -> Span:
        if end > self._length:
            raise EndOfInputError(self.__error("Unexpected end of input"))
        return Span(start, end)

    def __error(self, msg: str) -> str:
        if self._index == 0:
            prefix = ""
        else:
            prefix = self._input.get(0, self._index)

        caret_line = " " * len(prefix) + "^"
        return f"{msg} at {self._index}\n{self._input}\n{caret_line}"

    def error(self, msg: str) -> GlobSyntaxError:
        return GlobSyntaxError(self.__error(msg))

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self._input.get(self._index, self._length)})"
        )


class WeakCursor(Cursor):
    def __init__(self, cursor: Cursor) -> None:
        _input = cursor._input.get(start=cursor._index, end=cursor._length)
        super().__init__(_input)
