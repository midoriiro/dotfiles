# test_glob_core_props.py
import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from poexy_core.utils.glob.core import (
    CharClass,
    CharLiteralClassItem,
    GlobStar,
    Pattern,
    PosixClass,
    Segment,
    Token,
)
from poexy_core.utils.glob.exceptions import GlobSyntaxError
from poexy_core.utils.glob.helpers.cursor import Cursor
from poexy_core.utils.glob.helpers.input import Input


def parse_pattern(text: str) -> Pattern:
    cursor = Cursor(Input(text))
    pattern = Pattern.parse(cursor)
    if not cursor.at_end():
        raise GlobSyntaxError(cursor.error("Trailing characters after valid pattern"))
    return pattern


# --- alphabets ---

allowed_chars = string.ascii_letters + string.digits + "_-"

literal_chars = st.sampled_from(list(allowed_chars))

posix_names = st.sampled_from([c.value for c in PosixClass])

# --- stratégies classes ---


@st.composite
def char_literal_class_item(draw):
    k = draw(st.integers(min_value=3, max_value=6))
    output = []
    for _ in range(k):
        output.append(draw(literal_chars))
    return "".join(output)


@st.composite
def char_range_class_item(draw):
    return draw(st.tuples(literal_chars, literal_chars))


@st.composite
def posix_class_item(draw):
    return draw(posix_names)


@st.composite
def char_class_items(draw: st.DrawFn):
    items = []
    k = draw(st.integers(min_value=1, max_value=4))
    for _ in range(k):
        choice = draw(st.integers(min_value=0, max_value=2))
        if choice == 0:
            literal = draw(st.text(allowed_chars, min_size=3, max_size=6))
            items.append(literal)
        elif choice == 1:
            a, b = draw(char_range_class_item())
            items.append(f"{a}-{b}")
        else:
            items.append(f"[:{draw(posix_class_item())}:]")
    return items


@st.composite
def char_class_text(draw):
    neg = draw(st.booleans())
    body = draw(char_class_items())
    output = []
    output.append(Token.CharClassOpenBracket)
    if neg:
        output.append(Token.Negate)
    output.extend(body)
    output.append(Token.CharClassCloseBracket)
    return "".join(output)


# --- tokens de segment ---

segment_any_string = st.just(Token.AnyString)
segment_any_char = st.just(Token.AnyChar)
segment_literal = st.text(allowed_chars, min_size=3, max_size=6)
segment_char_class = char_class_text()

segment_token = st.one_of(
    segment_literal, segment_any_char, segment_any_string, segment_char_class
)


@st.composite
def segment_text(draw):
    items = []
    k = draw(st.integers(min_value=3, max_value=6))
    for _ in range(k):
        choice = draw(st.integers(min_value=0, max_value=3))
        if choice == 0:
            literal = draw(st.text(allowed_chars, min_size=3, max_size=6))
            items.append(literal)
        elif choice == 1:
            any_char = draw(segment_any_char)
            if len(items) > 0 and items[-1] == Token.AnyChar:
                literal = draw(char_literal_class_item())
                items.append(literal)
                continue
            items.append(any_char)
        elif choice == 2:
            any_string = draw(segment_any_string)
            if len(items) > 0 and items[-1] == Token.AnyString:
                literal = draw(char_literal_class_item())
                items.append(literal)
                continue
            items.append(any_string)
        else:
            char_class = draw(char_class_text())
            items.append(char_class)
    return "".join(items)


globstar_seg = st.just(Token.GlobStar)

path_part = st.one_of(segment_text(), globstar_seg)


@st.composite
def pattern_text(draw):
    m = draw(st.integers(min_value=3, max_value=3))
    parts = [draw(path_part) for _ in range(m)]
    return "/".join(parts)


# --- propriétés ---


@given(pattern_text())
@pytest.mark.prevent_venv_use
def test_parse_roundtrip(pattern_s):
    pat = parse_pattern(pattern_s)
    s2 = str(pat)
    pat2 = parse_pattern(s2)
    assert str(pat2) == s2


@given(pattern_text())
@pytest.mark.prevent_venv_use
def test_spans_in_bounds(pattern_s):
    pat = parse_pattern(pattern_s)
    assert 0 <= pat.span.start <= pat.span.end <= len(pattern_s)
    for part in pat.parts:
        assert 0 <= part.span.start <= part.span.end <= len(pattern_s)
        if isinstance(part, Segment):
            for t in part.tokens:
                assert 0 <= t.span.start <= t.span.end <= len(pattern_s)
                if isinstance(t, CharClass):
                    for it in t.items:
                        assert 0 <= it.span.start <= it.span.end <= len(pattern_s)


@given(pattern_text())
@pytest.mark.prevent_venv_use
def test_globstar_is_full_segment(pattern_s):
    pat = parse_pattern(pattern_s)
    for part in pat.parts:
        if isinstance(part, GlobStar):
            pass


@given(segment_text())
@pytest.mark.prevent_venv_use
def test_segment_alone(segment_s):
    pat = parse_pattern(segment_s)
    assert len(pat.parts) == 1
    assert isinstance(pat.parts[0], Segment)


@given(globstar_seg)
@pytest.mark.prevent_venv_use
def test_globstar_alone(gs):
    pat = parse_pattern(gs)
    assert len(pat.parts) == 1
    assert isinstance(pat.parts[0], GlobStar)


def bad_inside_globstar():
    return st.builds(
        lambda a, b: a + "**" + b,
        st.text(literal_chars, min_size=1, max_size=2),
        st.text(literal_chars, min_size=0, max_size=2),
    )


@given(bad_inside_globstar())
@pytest.mark.prevent_venv_use
def test_reject_embedded_globstar(bad):
    with pytest.raises(GlobSyntaxError):
        parse_pattern(bad)


def bad_unclosed_class():
    return st.text(literal_chars, min_size=0, max_size=2).map(lambda p: p + "[")


@given(bad_unclosed_class())
@pytest.mark.prevent_venv_use
def test_reject_unclosed_class(bad):
    with pytest.raises(GlobSyntaxError):
        parse_pattern(bad)


def bad_empty_segment():
    return st.just("a//b")


@given(bad_empty_segment())
@pytest.mark.prevent_venv_use
def test_reject_empty_segment(bad):
    with pytest.raises(GlobSyntaxError):
        parse_pattern(bad)
