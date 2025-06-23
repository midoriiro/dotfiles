import pytest
from pydantic import ValidationError
from assertpy import assert_that

from ignite.models.container import URL, URLScheme


class TestValidURL:
    """Test cases for valid URL configurations."""

    @pytest.mark.parametrize("scheme,host,port", [
        (URLScheme.SSH, "localhost", 22),
        (URLScheme.SSH, "192.168.1.1", 2222),
        (URLScheme.TCP, "example.com", 8080),
        (URLScheme.TCP, "10.0.0.1", 443),
        (URLScheme.SSH, "server.example.org", 2200),
        (URLScheme.TCP, "api.example.com", 3000),
    ])
    def test_valid_url_with_port(self, scheme, host, port):
        """Test that valid URLs with ports are accepted."""
        url = URL(scheme=scheme, host=host, port=port)
        assert_that(url.scheme).is_equal_to(scheme)
        assert_that(url.host).is_equal_to(host)
        assert_that(url.port).is_equal_to(port)

    @pytest.mark.parametrize("scheme,host", [
        (URLScheme.SSH, "localhost"),
        (URLScheme.SSH, "192.168.1.1"),
        (URLScheme.TCP, "example.com"),
        (URLScheme.TCP, "10.0.0.1"),
        (URLScheme.SSH, "server.example.org"),
        (URLScheme.TCP, "api.example.com"),
    ])
    def test_valid_url_without_port(self, scheme, host):
        """Test that valid URLs without ports are accepted."""
        url = URL(scheme=scheme, host=host)
        assert_that(url.scheme).is_equal_to(scheme)
        assert_that(url.host).is_equal_to(host)
        assert_that(url.port).is_none()

    def test_url_with_ssh_scheme(self):
        """Test that URLs with SSH scheme are accepted."""
        url = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        assert_that(url.scheme).is_equal_to(URLScheme.SSH)
        assert_that(url.host).is_equal_to("localhost")
        assert_that(url.port).is_equal_to(22)

    def test_url_with_tcp_scheme(self):
        """Test that URLs with TCP scheme are accepted."""
        url = URL(scheme=URLScheme.TCP, host="example.com", port=8080)
        assert_that(url.scheme).is_equal_to(URLScheme.TCP)
        assert_that(url.host).is_equal_to("example.com")
        assert_that(url.port).is_equal_to(8080)


class TestURLValidation:
    """Test cases for URL validation rules."""

    def test_url_with_invalid_scheme(self):
        """Test that URLs with invalid schemes are rejected."""
        with pytest.raises(ValidationError, match="Input should be 'ssh' or 'tcp'"):
            URL(scheme="http", host="localhost")

    def test_url_with_empty_host(self):
        """Test that URLs with empty hosts are rejected."""
        with pytest.raises(ValidationError, match="should have at least 1 character"):
            URL(scheme=URLScheme.SSH, host="")

    def test_url_with_too_long_host(self):
        """Test that URLs with hosts longer than 256 characters are rejected."""
        long_host = "a" * 257
        with pytest.raises(ValidationError, match="should have at most 256 characters"):
            URL(scheme=URLScheme.SSH, host=long_host)

    def test_url_with_port_below_minimum(self):
        """Test that URLs with ports below 1 are rejected."""
        with pytest.raises(ValidationError, match="should be greater than or equal to 1"):
            URL(scheme=URLScheme.SSH, host="localhost", port=0)

    def test_url_with_port_above_maximum(self):
        """Test that URLs with ports above 65535 are rejected."""
        with pytest.raises(ValidationError, match="should be less than or equal to 65535"):
            URL(scheme=URLScheme.SSH, host="localhost", port=65536)

    def test_url_with_negative_port(self):
        """Test that URLs with negative ports are rejected."""
        with pytest.raises(ValidationError, match="should be greater than or equal to 1"):
            URL(scheme=URLScheme.SSH, host="localhost", port=-1)

    def test_url_with_missing_scheme(self):
        """Test that URLs with missing schemes are rejected."""
        with pytest.raises(ValidationError, match="Field required"):
            URL(host="localhost")

    def test_url_with_missing_host(self):
        """Test that URLs with missing hosts are rejected."""
        with pytest.raises(ValidationError, match="Field required"):
            URL(scheme=URLScheme.SSH)


class TestURLStringRepresentation:
    """Test cases for URL string representation."""

    @pytest.mark.parametrize("scheme,host,port,expected", [
        (URLScheme.SSH, "localhost", 22, "ssh://localhost:22"),
        (URLScheme.SSH, "192.168.1.1", 2222, "ssh://192.168.1.1:2222"),
        (URLScheme.TCP, "example.com", 8080, "tcp://example.com:8080"),
        (URLScheme.TCP, "10.0.0.1", 443, "tcp://10.0.0.1:443"),
        (URLScheme.SSH, "server.example.org", 2200, "ssh://server.example.org:2200"),
        (URLScheme.TCP, "api.example.com", 3000, "tcp://api.example.com:3000"),
    ])
    def test_url_string_with_port(self, scheme, host, port, expected):
        """Test that URLs with ports are stringified correctly."""
        url = URL(scheme=scheme, host=host, port=port)
        assert_that(str(url)).is_equal_to(expected)

    @pytest.mark.parametrize("scheme,host,expected", [
        (URLScheme.SSH, "localhost", "ssh://localhost"),
        (URLScheme.SSH, "192.168.1.1", "ssh://192.168.1.1"),
        (URLScheme.TCP, "example.com", "tcp://example.com"),
        (URLScheme.TCP, "10.0.0.1", "tcp://10.0.0.1"),
        (URLScheme.SSH, "server.example.org", "ssh://server.example.org"),
        (URLScheme.TCP, "api.example.com", "tcp://api.example.com"),
    ])
    def test_url_string_without_port(self, scheme, host, expected):
        """Test that URLs without ports are stringified correctly."""
        url = URL(scheme=scheme, host=host)
        assert_that(str(url)).is_equal_to(expected)

    def test_url_string_edge_case_minimum_port(self):
        """Test that URLs with minimum port (1) are stringified correctly."""
        url = URL(scheme=URLScheme.SSH, host="localhost", port=1)
        assert_that(str(url)).is_equal_to("ssh://localhost:1")

    def test_url_string_edge_case_maximum_port(self):
        """Test that URLs with maximum port (65535) are stringified correctly."""
        url = URL(scheme=URLScheme.TCP, host="localhost", port=65535)
        assert_that(str(url)).is_equal_to("tcp://localhost:65535")


class TestURLEdgeCases:
    """Test cases for URL edge cases."""

    def test_url_with_minimum_valid_port(self):
        """Test that URLs with minimum valid port (1) are accepted."""
        url = URL(scheme=URLScheme.SSH, host="localhost", port=1)
        assert_that(url.scheme).is_equal_to(URLScheme.SSH)
        assert_that(url.host).is_equal_to("localhost")
        assert_that(url.port).is_equal_to(1)

    def test_url_with_maximum_valid_port(self):
        """Test that URLs with maximum valid port (65535) are accepted."""
        url = URL(scheme=URLScheme.TCP, host="localhost", port=65535)
        assert_that(url.scheme).is_equal_to(URLScheme.TCP)
        assert_that(url.host).is_equal_to("localhost")
        assert_that(url.port).is_equal_to(65535)

    def test_url_with_single_character_host(self):
        """Test that URLs with single character hosts are accepted."""
        url = URL(scheme=URLScheme.SSH, host="a")
        assert_that(url.scheme).is_equal_to(URLScheme.SSH)
        assert_that(url.host).is_equal_to("a")
        assert_that(url.port).is_none()

    def test_url_with_maximum_length_host(self):
        """Test that URLs with maximum length hosts (256 characters) are accepted."""
        long_host = "a" * 256
        url = URL(scheme=URLScheme.TCP, host=long_host, port=8080)
        assert_that(url.scheme).is_equal_to(URLScheme.TCP)
        assert_that(url.host).is_equal_to(long_host)
        assert_that(url.port).is_equal_to(8080)

    def test_url_with_ipv4_address(self):
        """Test that URLs with IPv4 addresses are accepted."""
        url = URL(scheme=URLScheme.SSH, host="192.168.1.100", port=22)
        assert_that(url.scheme).is_equal_to(URLScheme.SSH)
        assert_that(url.host).is_equal_to("192.168.1.100")
        assert_that(url.port).is_equal_to(22)

    def test_url_with_domain_name(self):
        """Test that URLs with domain names are accepted."""
        url = URL(scheme=URLScheme.TCP, host="api.example.com", port=443)
        assert_that(url.scheme).is_equal_to(URLScheme.TCP)
        assert_that(url.host).is_equal_to("api.example.com")
        assert_that(url.port).is_equal_to(443)

    def test_url_with_subdomain(self):
        """Test that URLs with subdomains are accepted."""
        url = URL(scheme=URLScheme.SSH, host="dev.server.example.org", port=2200)
        assert_that(url.scheme).is_equal_to(URLScheme.SSH)
        assert_that(url.host).is_equal_to("dev.server.example.org")
        assert_that(url.port).is_equal_to(2200)


class TestURLModelBehavior:
    """Test cases for URL model behavior."""

    def test_url_model_construction(self):
        """Test that URL models can be constructed correctly."""
        url = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        assert_that(url).is_instance_of(URL)
        assert_that(url.scheme).is_instance_of(URLScheme)
        assert_that(url.host).is_instance_of(str)
        assert_that(url.port).is_instance_of(int)

    def test_url_model_construction_without_port(self):
        """Test that URL models can be constructed without port."""
        url = URL(scheme=URLScheme.TCP, host="example.com")
        assert_that(url).is_instance_of(URL)
        assert_that(url.scheme).is_instance_of(URLScheme)
        assert_that(url.host).is_instance_of(str)
        assert_that(url.port).is_none()

    def test_url_model_equality(self):
        """Test that URL models with same values are equal."""
        url1 = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        url2 = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        assert_that(url1).is_equal_to(url2)

    def test_url_model_inequality(self):
        """Test that URL models with different values are not equal."""
        url1 = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        url2 = URL(scheme=URLScheme.TCP, host="localhost", port=22)
        assert_that(url1).is_not_equal_to(url2)

    def test_url_model_repr(self):
        """Test that URL models have a meaningful string representation."""
        url = URL(scheme=URLScheme.SSH, host="localhost", port=22)
        repr_str = repr(url)
        assert_that(repr_str).contains("URL")
        assert_that(repr_str).contains("ssh")
        assert_that(repr_str).contains("localhost")
        assert_that(repr_str).contains("22")


class TestURLSchemeEnum:
    """Test cases for URLScheme enum."""

    def test_url_scheme_values(self):
        """Test that URLScheme enum has correct values."""
        assert_that(URLScheme.SSH).is_equal_to("ssh")
        assert_that(URLScheme.TCP).is_equal_to("tcp")

    def test_url_scheme_iteration(self):
        """Test that URLScheme enum can be iterated."""
        schemes = list(URLScheme)
        assert_that(schemes).contains("ssh")
        assert_that(schemes).contains("tcp")
        assert_that(schemes).is_length(2)
