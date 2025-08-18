from typing import Self, SupportsIndex


class SliceView:
    def __init__(self, base: str, start: int, end: int) -> None:
        if start < 0:
            raise ValueError("Start index must be positive")
        if end < 0:
            raise ValueError("End index must be positive")
        if start > len(base):
            raise ValueError("Start index out of range")
        if end > len(base):
            raise ValueError("End index out of range")
        if start > end:
            raise ValueError("Start index must be less than end index")
        if end < start:
            raise ValueError("End index must be greater than start index")
        if start == end:
            raise ValueError("Start and end indices cannot be the same")

        self._base = base
        self.__start = start
        self.__end = end

    def __len__(self) -> int:
        return self.__end - self.__start

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, str):
            return False

        if len(self) != len(other):
            return False

        return self._base.startswith(other, self.__start, self.__end)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return self._base[self.__start : self.__end]  # noqa: E203

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}([s={self.__start}, e={self.__end}], {self})"

    def get(self, start: int, end: int) -> Self:
        return SliceView(self._base, self.__start + start, self.__start + end)

    def startswith(self, prefix: str, start: SupportsIndex = 0) -> bool:
        if start < 0 or start > len(self):
            raise ValueError("Start index out of range")
        return self._base.startswith(prefix, self.__start + start, self.__end)
