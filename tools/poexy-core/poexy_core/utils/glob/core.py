from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Self, Type, Union

from poexy_core.utils.enums import ExtendedEnum
from poexy_core.utils.glob.exceptions import EndOfInputError, GlobSyntaxError
from poexy_core.utils.glob.helpers.cursor import Cursor
from poexy_core.utils.glob.helpers.slice import SliceView
from poexy_core.utils.glob.helpers.span import Span


class Token(str, ExtendedEnum):
    Negate = "!"
    GlobStar = "**"
    AnyChar = "?"
    AnyString = "*"
    CharClassOpenBracket = "["
    CharClassCloseBracket = "]"
    CharRangeSeparator = "-"
    PosixClassOpenBracket = "[:"
    PosixClassCloseBracket = ":]"
    PathSeparator = "/"
    PathSeparatorAlt = "\\"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return super().__eq__(other)
        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        if isinstance(other, str):
            return super().__ne__(other)
        return super().__ne__(other.value)

    def __str__(self) -> str:
        return self.value


class PosixClass(Enum):
    ALNUM = "alnum"
    ALPHA = "alpha"
    BLANK = "blank"
    CNTRL = "cntrl"
    DIGIT = "digit"
    GRAPH = "graph"
    LOWER = "lower"
    PRINT = "print"
    PUNCT = "punct"
    SPACE = "space"
    UPPER = "upper"
    XDIGIT = "xdigit"

    @staticmethod
    def from_value(value: str) -> "PosixClass":
        try:
            return PosixClass(value)
        except ValueError as e:
            raise GlobSyntaxError(f"Unknown POSIX class: {value}") from e


class Node(ABC):
    def __init__(self, span: Span) -> None:
        self.span = span

    @classmethod
    @abstractmethod
    def parse(cls, cursor: Cursor) -> Self:
        raise NotImplementedError

    @classmethod
    def parse_one_of(cls, cursor: Cursor, nodes: List[Type[Self]]) -> Self:
        for node_type in nodes:
            try:
                node = node_type.parse(cursor.as_weak())
                cursor.advance(node.span.length)
                return node
            except GlobSyntaxError:
                continue

        type_names = ", ".join(node_type.__name__ for node_type in nodes)

        raise cursor.error(f"Expected one of the following nodes: {type_names}")

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"


class CharLiteralClassItem(Node):
    def __init__(self, value: List[SliceView], span: Span) -> None:
        super().__init__(span)
        self.value = value

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        start = cursor.position()
        chars: List[SliceView] = []

        while not cursor.at_end():
            char = cursor.consume().output

            if cursor.at_end() and char == Token.CharClassCloseBracket:
                cursor.rewind()
                break

            next_char = cursor.peek().output

            if (
                char == Token.CharClassCloseBracket
                and next_char != Token.CharClassCloseBracket
            ):
                cursor.rewind()
                break

            if (
                char == Token.CharClassCloseBracket
                and next_char == Token.CharClassCloseBracket
            ):
                chars.append(char)
                break

            chars.append(char)

        end = cursor.position()

        return cls(chars, Span(start, end))

    def __str__(self) -> str:
        return "".join(str(value) for value in self.value)


class CharRangeClassItem(Node):
    def __init__(self, start: SliceView, end: SliceView, span: Span) -> None:
        super().__init__(span)
        self.start = start
        self.end = end

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        start = cursor.consume(1)
        cursor.expect(Token.CharRangeSeparator)
        end = cursor.consume(1)
        return cls(start.output, end.output, Span(start.span.start, end.span.end))

    def __str__(self) -> str:
        return f"{self.start}{Token.CharRangeSeparator}{self.end}"


class PosixClassItem(Node):
    def __init__(self, cls: SliceView, span: Span) -> None:
        super().__init__(span)
        self.cls = cls

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        start = cursor.expect(Token.PosixClassOpenBracket)
        name = cursor.until(Token.PosixClassCloseBracket)
        end = cursor.expect(Token.PosixClassCloseBracket)
        return cls(name.output, Span(start.span.start, end.span.end))

    def __str__(self) -> str:
        return f"{Token.PosixClassOpenBracket}{self.cls}{Token.PosixClassCloseBracket}"


ClassItem = Union[CharLiteralClassItem, CharRangeClassItem, PosixClassItem]


class CharClass(Node):
    def __init__(self, items: List[ClassItem], negated: bool, span: Span) -> None:
        super().__init__(span)
        self.items = items
        self.negated = negated

    @staticmethod
    def __class_item_types() -> List[Type[ClassItem]]:
        return [PosixClassItem, CharRangeClassItem, CharLiteralClassItem]

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        start = cursor.expect(Token.CharClassOpenBracket)

        items: List[ClassItem] = []

        if cursor.peek().output == Token.Negate:
            cursor.advance(1)
            negated = True
        else:
            negated = False

        while not cursor.at_end():
            item = cls.parse_one_of(cursor, cls.__class_item_types())
            items.append(item)
            if cursor.peek().output == Token.CharClassCloseBracket:
                break

        end = cursor.expect(Token.CharClassCloseBracket)

        return cls(
            items=items,
            negated=negated,
            span=Span(start.span.start, end.span.end),
        )

    def __str__(self) -> str:
        items = "".join(str(item) for item in self.items)
        if self.negated:
            items = Token.Negate + items
        return f"{Token.CharClassOpenBracket}{items}{Token.CharClassCloseBracket}"


class Literal(Node):
    def __init__(self, token: List[SliceView], span: Span) -> None:
        super().__init__(span)
        self.token = token

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        start = cursor.position()
        token: List[SliceView] = []
        separators = [
            Token.AnyChar,
            Token.AnyString,
            Token.CharClassOpenBracket,
            Token.PathSeparator,
            Token.PathSeparatorAlt,
        ]
        while not cursor.at_end():
            char = cursor.peek().output

            if char in separators:
                break

            token.append(cursor.consume().output)

        if not token:
            raise GlobSyntaxError(cursor.error("Empty literal segment"))

        return cls(token, Span(start, cursor.position()))

    def __str__(self) -> str:
        return "".join(str(token) for token in self.token)


class AnyChar(Node):
    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        token = cursor.expect(Token.AnyChar)
        return cls(token.span)

    def __str__(self) -> str:
        return Token.AnyChar.value


class AnyString(Node):
    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        token = cursor.expect(Token.AnyString)
        return cls(token.span)

    def __str__(self) -> str:
        return Token.AnyString.value


SegmentToken = Union[Literal, AnyChar, AnyString, CharClass]


class Segment(Node):
    def __init__(self, tokens: List[SegmentToken], span: Span) -> None:
        super().__init__(span)
        self.tokens = tokens

    @staticmethod
    def __token_types() -> List[Type[SegmentToken]]:
        return [AnyChar, AnyString, CharClass, Literal]

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        start = cursor.position()
        tokens: List[SegmentToken] = []
        separators = [
            Token.PathSeparator,
            Token.PathSeparatorAlt,
        ]

        while not cursor.at_end():
            char = cursor.peek().output

            if char in separators:
                break

            token = cls.parse_one_of(cursor, cls.__token_types())
            tokens.append(token)

        if not tokens or len(tokens) == 0:
            raise cursor.error("Unexpected end of segment")

        end = cursor.position()

        return cls(tokens=tokens, span=Span(start, end))

    def __str__(self) -> str:
        return "".join(str(token) for token in self.tokens)


class GlobStar(Node):
    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        token = cursor.expect(Token.GlobStar)
        return cls(token.span)

    def __str__(self) -> str:
        return Token.GlobStar.value


class Separator(Node):
    def __init__(self, token: SliceView, span: Span) -> None:
        super().__init__(span)
        self.token = token

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        separators = [Token.PathSeparator, Token.PathSeparatorAlt]
        token = cursor.peek()

        if token.output not in separators:
            raise cursor.error("Unexpected separator")

        cursor.advance(1)

        return cls(token.output, token.span)

    def __str__(self) -> str:
        return str(self.token)


PathPart = Union[Segment, GlobStar]


class Pattern(Node):
    def __init__(self, parts: List[PathPart], negated: bool, span: Span) -> None:
        super().__init__(span)
        self.parts = parts
        self.negated = negated

    @staticmethod
    def __path_part_types() -> List[Type[PathPart]]:
        return [GlobStar, Segment]

    @classmethod
    def parse(cls, cursor: Cursor) -> Self:
        start = cursor.position()
        parts: List[PathPart] = []

        if cursor.peek().output == Token.Negate:
            cursor.advance(1)
            negated = True
        else:
            negated = False

        while not cursor.at_end():
            part = cls.parse_one_of(cursor, cls.__path_part_types())

            parts.append(part)

            try:
                separator = Separator.parse(cursor)
                parts.append(separator)
            except EndOfInputError:
                break

        if not parts or len(parts) == 0:
            raise cursor.error("Unexpected end of pattern")

        end = cursor.position()

        return cls(parts=parts, negated=negated, span=Span(start, end))

    def __str__(self) -> str:
        parts = "".join(str(part) for part in self.parts)

        if self.negated:
            parts = Token.Negate + parts

        return parts
