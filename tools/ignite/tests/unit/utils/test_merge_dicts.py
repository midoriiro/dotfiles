import pytest
from assertpy import assert_that

from ignite.utils import merge_dicts


def test_basic_merge():
    """Test basic dictionary merging."""
    a = {"x": 1, "y": 2}
    b = {"z": 3, "w": 4}

    merge_dicts(a, b)

    expected = {"x": 1, "y": 2, "z": 3, "w": 4}
    assert_that(a).is_equal_to(expected)


def test_overwrite_existing_keys():
    """Test that existing keys are overwritten."""
    a = {"x": 1, "y": 2}
    b = {"x": 10, "z": 3}

    merge_dicts(a, b)

    expected = {"x": 10, "y": 2, "z": 3}
    assert_that(a).is_equal_to(expected)


def test_nested_dictionary_merge():
    """Test merging of nested dictionaries."""
    a = {"x": 1, "y": {"a": 1, "b": 2}}
    b = {"y": {"b": 3, "c": 4}, "z": 5}

    merge_dicts(a, b)

    expected = {"x": 1, "y": {"a": 1, "b": 3, "c": 4}, "z": 5}
    assert_that(a).is_equal_to(expected)


def test_deep_nested_dictionary_merge():
    """Test merging of deeply nested dictionaries."""
    a = {"level1": {"level2": {"level3": {"a": 1, "b": 2}}}}
    b = {"level1": {"level2": {"level3": {"b": 3, "c": 4}}}}

    merge_dicts(a, b)

    expected = {"level1": {"level2": {"level3": {"a": 1, "b": 3, "c": 4}}}}
    assert_that(a).is_equal_to(expected)


def test_list_concatenation():
    """Test that lists are concatenated."""
    a = {"items": [1, 2, 3]}
    b = {"items": [4, 5, 6]}

    merge_dicts(a, b)

    expected = {"items": [1, 2, 3, 4, 5, 6]}
    assert_that(a).is_equal_to(expected)


def test_mixed_types_merge():
    """Test merging with different data types."""
    a = {
        "string": "hello",
        "number": 42,
        "boolean": True,
        "list": [1, 2],
        "dict": {"a": 1},
    }
    b = {
        "string": "world",
        "number": 100,
        "boolean": False,
        "list": [3, 4],
        "dict": {"b": 2},
    }

    merge_dicts(a, b)

    expected = {
        "string": "world",
        "number": 100,
        "boolean": False,
        "list": [1, 2, 3, 4],
        "dict": {"a": 1, "b": 2},
    }
    assert_that(a).is_equal_to(expected)


def test_empty_dictionary_merge():
    """Test merging with empty dictionaries."""
    a = {"x": 1, "y": 2}
    b = {}

    merge_dicts(a, b)

    expected = {"x": 1, "y": 2}
    assert_that(a).is_equal_to(expected)


def test_merge_into_empty_dictionary():
    """Test merging into an empty dictionary."""
    a = {}
    b = {"x": 1, "y": 2}

    merge_dicts(a, b)

    expected = {"x": 1, "y": 2}
    assert_that(a).is_equal_to(expected)


def test_both_empty_dictionaries():
    """Test merging two empty dictionaries."""
    a = {}
    b = {}

    merge_dicts(a, b)

    expected = {}
    assert_that(a).is_equal_to(expected)


def test_nested_list_merge():
    """Test merging dictionaries with nested lists."""
    a = {"config": {"items": [{"id": 1}, {"id": 2}]}}
    b = {"config": {"items": [{"id": 3}, {"id": 4}]}}

    merge_dicts(a, b)

    expected = {"config": {"items": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]}}
    assert_that(a).is_equal_to(expected)


def test_dict_overwrites_list():
    """Test that dict overwrites list when types conflict."""
    a = {"key": [1, 2, 3]}
    b = {"key": {"a": 1, "b": 2}}

    merge_dicts(a, b)

    expected = {"key": {"a": 1, "b": 2}}
    assert_that(a).is_equal_to(expected)


def test_list_overwrites_dict():
    """Test that list overwrites dict when types conflict."""
    a = {"key": {"a": 1, "b": 2}}
    b = {"key": [1, 2, 3]}

    merge_dicts(a, b)

    expected = {"key": [1, 2, 3]}
    assert_that(a).is_equal_to(expected)


def test_preserves_original_structure():
    """Test that original structure is preserved when no conflicts."""
    a = {"level1": {"level2": {"a": 1}}}
    b = {"level1": {"level2": {"b": 2}}}

    merge_dicts(a, b)

    expected = {"level1": {"level2": {"a": 1, "b": 2}}}
    assert_that(a).is_equal_to(expected)


def test_complex_nested_structure():
    """Test merging complex nested structures."""
    a = {
        "settings": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "options": ["ssl", "timeout"],
            },
            "cache": {"enabled": True, "ttl": 3600},
        },
        "features": ["auth", "logging"],
    }

    b = {
        "settings": {
            "database": {
                "port": 5433,
                "options": ["pooling"],
                "credentials": {"user": "admin"},
            },
            "cache": {"ttl": 7200, "max_size": 1000},
        },
        "features": ["monitoring"],
        "debug": True,
    }

    merge_dicts(a, b)

    expected = {
        "settings": {
            "database": {
                "host": "localhost",
                "port": 5433,
                "options": ["ssl", "timeout", "pooling"],
                "credentials": {"user": "admin"},
            },
            "cache": {"enabled": True, "ttl": 7200, "max_size": 1000},
        },
        "features": ["auth", "logging", "monitoring"],
        "debug": True,
    }
    assert_that(a).is_equal_to(expected)


def test_function_modifies_in_place():
    """Test that the function modifies the first dictionary in place."""
    a = {"x": 1}
    b = {"y": 2}

    # Store reference to original dictionary
    original_a = a

    merge_dicts(a, b)

    # Check that the same object was modified
    assert_that(a).is_same_as(original_a)
    assert_that(a).contains_key("x")
    assert_that(a).contains_key("y")


def test_function_returns_none():
    """Test that the function returns None."""
    a = {"x": 1}
    b = {"y": 2}

    result = merge_dicts(a, b)

    assert_that(result).is_none()
