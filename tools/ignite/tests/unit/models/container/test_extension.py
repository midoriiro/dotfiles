import pytest
from assertpy import assert_that
from pydantic import BaseModel, ValidationError

from ignite.models.container import Extension


class TestModel(BaseModel):
    """Test model with Extension field."""

    extension: Extension


class TestValidExtensions:
    """Test cases for valid extension patterns."""

    @pytest.mark.parametrize(
        "extension",
        [
            "ms-python.python",
            "ms-vscode.vscode-json",
            "ms-vscode.vscode-typescript",
            "ms-vscode.vscode-java",
            "ms-vscode.vscode-cpp",
            "ms-vscode.vscode-csharp",
            "ms-vscode.vscode-go",
            "ms-vscode.vscode-rust",
            "ms-vscode.vscode-php",
            "ms-vscode.vscode-ruby",
            "ms-vscode.vscode-scala",
            "ms-vscode.vscode-swift",
            "ms-vscode.vscode-kotlin",
            "ms-vscode.vscode-dart",
            "ms-vscode.vscode-elixir",
            "ms-vscode.vscode-clojure",
            "ms-vscode.vscode-haskell",
            "ms-vscode.vscode-ocaml",
            "ms-vscode.vscode-fsharp",
            "ms-vscode.vscode-erlang",
        ],
    )
    def test_microsoft_extensions(self, extension):
        """Test that valid Microsoft extensions are accepted."""
        model = TestModel(extension=extension)
        assert_that(model.extension).is_equal_to(extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "bradlc.vscode-tailwindcss",
            "esbenp.prettier-vscode",
            "ms-vscode.vscode-eslint",
            "ms-vscode.vscode-prettier",
            "ms-vscode.vscode-tslint",
            "ms-vscode.vscode-stylelint",
            "ms-vscode.vscode-sass",
            "ms-vscode.vscode-less",
            "ms-vscode.vscode-stylus",
            "ms-vscode.vscode-postcss",
        ],
    )
    def test_popular_extensions(self, extension):
        """Test that popular third-party extensions are accepted."""
        model = TestModel(extension=extension)
        assert_that(model.extension).is_equal_to(extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "user123.extension-name",
            "test-user.test-extension",
            "dev-user.dev-extension",
            "my-org.my-extension",
            "company-name.product-name",
        ],
    )
    def test_custom_extensions(self, extension):
        """Test that custom extensions with valid patterns are accepted."""
        model = TestModel(extension=extension)
        assert_that(model.extension).is_equal_to(extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "a.b",
            "ab.cd",
            "abc.def",
            "test.extension",
            "very-long-publisher-name.very-long-extension-name",
        ],
    )
    def test_edge_cases(self, extension):
        """Test edge cases with minimal and maximal valid extensions."""
        model = TestModel(extension=extension)
        assert_that(model.extension).is_equal_to(extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "Test.Extension",
            "TEST.EXTENSION",
            "TestUser.TestExtension",
            "MyOrg.MyExtension",
        ],
    )
    def test_mixed_case(self, extension):
        """Test that extensions with mixed case are accepted."""
        model = TestModel(extension=extension)
        assert_that(model.extension).is_equal_to(extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "user123.extension456",
            "test-123.test-456",
            "user_123.extension_456",
            "v1.extension-v2",
        ],
    )
    def test_with_numbers(self, extension):
        """Test that extensions with numbers are accepted."""
        model = TestModel(extension=extension)
        assert_that(model.extension).is_equal_to(extension)


class TestInvalidExtensionFormat:
    """Test cases for invalid extension format patterns."""

    @pytest.mark.parametrize(
        "extension",
        [
            "ms-python",  # Missing dot and second part
            "python",  # Missing publisher
            ".python",  # Missing publisher, only dot and name
            "ms-python.",  # Missing name after dot
            "ms.python.extra",  # Too many parts
            "ms..python",  # Double dot
            "ms.python.",  # Trailing dot
            ".ms.python",  # Leading dot
        ],
    )
    def test_invalid_format(self, extension):
        """Test that extensions with invalid format are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)


class TestInvalidLength:
    """Test cases for invalid extension lengths."""

    def test_too_short(self):
        """Test that extensions shorter than 3 characters are rejected."""
        with pytest.raises(
            ValidationError, match="String should have at least 3 characters"
        ):
            TestModel(extension="ab")

    def test_too_long(self):
        """Test that extensions longer than 256 characters are rejected."""
        long_extension = "a" * 128 + "." + "b" * 128  # 257 characters total
        with pytest.raises(
            ValidationError, match="String should have at most 256 characters"
        ):
            TestModel(extension=long_extension)

    def test_empty_string(self):
        """Test that empty strings are rejected."""
        with pytest.raises(
            ValidationError, match="String should have at least 3 characters"
        ):
            TestModel(extension="")


class TestInvalidCharacters:
    """Test cases for invalid characters in extensions."""

    @pytest.mark.parametrize(
        "extension",
        [
            "ms-python@.python",
            "ms-python#.python",
            "ms-python$.python",
            "ms-python%.python",
            "ms-python&.python",
            "ms-python*.python",
            "ms-python+.python",
            "ms-python=.python",
            "ms-python/.python",
            "ms-python\\.python",
            "ms-python?.python",
            "ms-python!.python",
            "ms-python|.python",
            "ms-python~.python",
            "ms-python`.python",
            "ms-python'.python",
            'ms-python".python',
            "ms-python(.python",
            "ms-python).python",
            "ms-python[.python",
            "ms-python].python",
            "ms-python{.python",
            "ms-python}.python",
            "ms-python<.python",
            "ms-python>.python",
            "ms-python;.python",
            "ms-python:.python",
            "ms-python,.python",
        ],
    )
    def test_special_characters(self, extension):
        """Test that extensions with special characters are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "ms python.python",
            "ms-python.python name",
            "ms-python .python",
            "ms-python. python",
            " ms-python.python",
            "ms-python.python ",
            " ms-python.python ",
        ],
    )
    def test_spaces(self, extension):
        """Test that extensions with spaces are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "123ms.python",
            "0user.extension",
            "9org.product",
        ],
    )
    def test_starts_with_number(self, extension):
        """Test that extensions starting with numbers are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "_ms.python",
            "_user.extension",
            "_org.product",
        ],
    )
    def test_starts_with_underscore(self, extension):
        """Test that extensions starting with underscores are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "-ms.python",
            "-user.extension",
            "-org.product",
        ],
    )
    def test_starts_with_hyphen(self, extension):
        """Test that extensions starting with hyphens are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "ms-.python",
            "user-.extension",
            "org-.product",
        ],
    )
    def test_ends_with_hyphen(self, extension):
        """Test that extensions ending with hyphens are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)

    @pytest.mark.parametrize(
        "extension",
        [
            "ms_.python",
            "user_.extension",
            "org_.product",
        ],
    )
    def test_ends_with_underscore(self, extension):
        """Test that extensions ending with underscores are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)


class TestInvalidUnicode:
    """Test cases for invalid unicode characters."""

    @pytest.mark.parametrize(
        "extension",
        [
            "ms-python.pythön",
            "usér.extension",
            "sérvice.product",
            "café.extension",
            "naïve.product",
            "résumé.extension",
            "cœur.product",
            "façade.extension",
        ],
    )
    def test_unicode_characters(self, extension):
        """Test that extensions with unicode characters are rejected."""
        with pytest.raises(ValidationError, match="should match pattern"):
            TestModel(extension=extension)


class TestExtensionUsage:
    """Test cases for Extension usage in real scenarios."""

    def test_extension_in_extensions_model(self):
        """Test that Extension can be used in Extensions model."""
        from ignite.models.container import Extensions

        extensions = Extensions(vscode=["ms-python.python", "esbenp.prettier-vscode"])
        assert_that(extensions.vscode).is_length(2)
        assert_that(extensions.vscode[0]).is_equal_to("ms-python.python")
        assert_that(extensions.vscode[1]).is_equal_to("esbenp.prettier-vscode")

    def test_extension_compose_method(self):
        """Test that Extensions model compose method works correctly."""
        from ignite.models.container import Extensions

        extensions = Extensions(vscode=["ms-python.python", "esbenp.prettier-vscode"])
        composed = extensions.compose()

        expected = {
            "customizations": {
                "vscode": {"extensions": ["ms-python.python", "esbenp.prettier-vscode"]}
            }
        }
        assert_that(composed).is_equal_to(expected)
